// A Flexi effect in C++: speaks the protocol directly and reads and writes images in shared memory.
#include <arpa/inet.h>
#include <fcntl.h>
#include <netdb.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <unistd.h>

#include <algorithm>
#include <cctype>
#include <cerrno>
#include <csignal>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

using json = nlohmann::json;

static const char *IDENTIFIER = "com.example.cpp_invert";
static const int VERSION = 1;

struct Closed : std::runtime_error {
    Closed() : std::runtime_error("connection closed") {}
};

static std::string sys_error(const std::string &what) {
    return what + ": " + std::strerror(errno);
}

static std::string base64(const unsigned char *data, size_t n) {
    static const char *digits = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string out;
    for (size_t i = 0; i < n; i += 3) {
        uint32_t v = data[i] << 16 | (i + 1 < n ? data[i + 1] << 8 : 0) | (i + 2 < n ? data[i + 2] : 0);
        out += digits[v >> 18 & 63];
        out += digits[v >> 12 & 63];
        out += i + 1 < n ? digits[v >> 6 & 63] : '=';
        out += i + 2 < n ? digits[v & 63] : '=';
    }
    return out;
}

// A minimal WebSocket client (RFC 6455): enough for the host's local server.
class WebSocket {
public:
    explicit WebSocket(const std::string &url) {
        if (url.rfind("ws://", 0) != 0)
            throw std::runtime_error("FLEXI_SERVER_URL is not a ws:// URL: " + url);
        std::string rest = url.substr(5);
        size_t slash = rest.find('/');
        std::string hostport = rest.substr(0, slash);
        std::string path = slash == std::string::npos ? "/" : rest.substr(slash);
        size_t colon = hostport.rfind(':');
        std::string host = hostport.substr(0, colon);
        std::string port = colon == std::string::npos ? "80" : hostport.substr(colon + 1);

        addrinfo hints{}, *found = nullptr;
        hints.ai_socktype = SOCK_STREAM;
        if (int rc = getaddrinfo(host.c_str(), port.c_str(), &hints, &found))
            throw std::runtime_error(host + ": " + gai_strerror(rc));
        for (addrinfo *a = found; a && fd_ < 0; a = a->ai_next) {
            fd_ = socket(a->ai_family, a->ai_socktype, a->ai_protocol);
            if (fd_ >= 0 && connect(fd_, a->ai_addr, a->ai_addrlen) != 0) {
                ::close(fd_);
                fd_ = -1;
            }
        }
        freeaddrinfo(found);
        if (fd_ < 0)
            throw std::runtime_error(sys_error("cannot connect to " + url));

        unsigned char key[16];
        for (auto &b : key)
            b = static_cast<unsigned char>(rng_());
        std::string request = "GET " + path + " HTTP/1.1\r\nHost: " + hostport +
                              "\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: " +
                              base64(key, sizeof key) + "\r\nSec-WebSocket-Version: 13\r\n\r\n";
        write_all(request.data(), request.size());
        std::string response;
        while (response.size() < 4 || response.compare(response.size() - 4, 4, "\r\n\r\n") != 0) {
            char c;
            read_all(&c, 1);
            response += c;
        }
        if (response.find(" 101 ") == std::string::npos)
            throw std::runtime_error("WebSocket upgrade refused: " + response.substr(0, response.find('\r')));
    }

    ~WebSocket() {
        if (fd_ >= 0)
            ::close(fd_);
    }

    std::string receive() {
        std::string message;
        for (;;) {
            unsigned char head[2];
            read_all(head, 2);
            bool fin = head[0] & 0x80;
            int opcode = head[0] & 0x0f;
            uint64_t len = head[1] & 0x7f;
            if (len >= 126) {
                unsigned char ext[8];
                int n = len == 126 ? 2 : 8;
                read_all(ext, n);
                len = 0;
                for (int i = 0; i < n; i++)
                    len = len << 8 | ext[i];
            }
            unsigned char mask[4] = {0, 0, 0, 0};
            if (head[1] & 0x80)
                read_all(mask, 4);
            std::string payload(len, '\0');
            if (len)
                read_all(&payload[0], len);
            for (uint64_t i = 0; i < len; i++)
                payload[i] ^= mask[i % 4];

            if (opcode == 0x8)
                throw Closed();
            if (opcode == 0x9)
                send_frame(0xA, payload);
            if (opcode == 0x0 || opcode == 0x1 || opcode == 0x2) {
                message += payload;
                if (fin)
                    return message;
            }
        }
    }

    void send(const std::string &text) { send_frame(0x1, text); }

    void close() { send_frame(0x8, ""); }

private:
    int fd_ = -1;
    std::mt19937 rng_{std::random_device{}()};

    void write_all(const void *data, size_t n) {
        const char *p = static_cast<const char *>(data);
        while (n > 0) {
            ssize_t done = ::write(fd_, p, n);
            if (done < 0 && errno == EINTR)
                continue;
            if (done <= 0)
                throw Closed();
            p += done;
            n -= done;
        }
    }

    void read_all(void *data, size_t n) {
        char *p = static_cast<char *>(data);
        while (n > 0) {
            ssize_t done = ::read(fd_, p, n);
            if (done < 0 && errno == EINTR)
                continue;
            if (done <= 0)
                throw Closed();
            p += done;
            n -= done;
        }
    }

    // Client frames must be masked
    void send_frame(int opcode, const std::string &payload) {
        std::vector<unsigned char> frame{static_cast<unsigned char>(0x80 | opcode)};
        uint64_t len = payload.size();
        if (len < 126) {
            frame.push_back(0x80 | len);
        } else if (len < 65536) {
            frame.push_back(0x80 | 126);
            for (int i = 1; i >= 0; i--)
                frame.push_back(len >> (8 * i) & 0xff);
        } else {
            frame.push_back(0x80 | 127);
            for (int i = 7; i >= 0; i--)
                frame.push_back(len >> (8 * i) & 0xff);
        }
        unsigned char mask[4];
        for (auto &b : mask)
            b = static_cast<unsigned char>(rng_());
        frame.insert(frame.end(), mask, mask + 4);
        for (uint64_t i = 0; i < len; i++)
            frame.push_back(payload[i] ^ mask[i % 4]);
        write_all(frame.data(), frame.size());
    }
};

// One of the host's shared-memory buffers: the host creates and removes it, the effect only maps it
class SharedImage {
public:
    SharedImage(const std::string &name, size_t bytes) : size_(bytes) {
        int fd = shm_open(name.c_str(), O_RDWR, 0);
        if (fd < 0)
            throw std::runtime_error(sys_error("shm_open " + name));
        struct stat st;
        if (fstat(fd, &st) != 0 || static_cast<size_t>(st.st_size) < bytes) {
            ::close(fd);
            throw std::runtime_error("shared memory " + name + " is smaller than the image");
        }
        void *p = mmap(nullptr, bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
        ::close(fd);
        if (p == MAP_FAILED)
            throw std::runtime_error(sys_error("mmap " + name));
        pixels = static_cast<float *>(p);
    }
    ~SharedImage() { munmap(pixels, size_); }
    SharedImage(const SharedImage &) = delete;
    SharedImage &operator=(const SharedImage &) = delete;

    float *pixels;

private:
    size_t size_;
};

struct Rect {
    long x, y, width, height;
    explicit Rect(const json &r)
        : x(r.at("left")), y(r.at("top")), width(r.at("width")), height(r.at("height")) {}
};

static json describe() {
    return {
        {"process_mode", {{"linux", "shm"}, {"macos", "shm"}}},
        {"inputs", {{{"name", "src"}, {"label", "Source"}, {"type", "image"}, {"format", "3XFLOAT"}}}},
        {"outputs", {{{"name", "out"}, {"label", "Result"}, {"type", "image"}, {"format", "3XFLOAT"}}}},
        {"params", {{{"name", "mix"}, {"label", "Mix"}, {"type", "float"}, {"default", 1.0},
                     {"range", {0.0, 1.0, 0.01}}, {"animated", true},
                     {"tooltip", "How much of the inverted image to show."}, {"uilocation", {0, 0}}}}},
        {"help", "Inverts the image. Written in C++, to show Flexi is not limited to Python."},
    };
}

static json run_generate(const json &data) {
    const json &input = data.at("inputs").value("src:0", json());
    if (input.is_null())
        throw std::runtime_error("No source image");
    const json &output = data.at("output");
    // A rect can be the string "empty": nothing to render
    if (!input.at("rect").is_object() || !output.at("rect").is_object())
        return json::object();
    float mix = data.value("params", json::object()).value("mix", 1.0f);

    Rect in_rect(input.at("rect")), out_rect(output.at("rect"));
    SharedImage src(input.at("shm"), in_rect.width * in_rect.height * 3 * sizeof(float));
    SharedImage dst(output.at("shm"), out_rect.width * out_rect.height * 3 * sizeof(float));

    for (long y = 0; y < out_rect.height; y++) {
        long sy = out_rect.y + y - in_rect.y;
        for (long x = 0; x < out_rect.width; x++) {
            long sx = out_rect.x + x - in_rect.x;
            float *out = dst.pixels + (y * out_rect.width + x) * 3;
            if (sy < 0 || sy >= in_rect.height || sx < 0 || sx >= in_rect.width) {
                std::fill(out, out + 3, 0.0f);
                continue;
            }
            const float *in = src.pixels + (sy * in_rect.width + sx) * 3;
            for (int c = 0; c < 3; c++)
                out[c] = in[c] + mix * (1.0f - 2.0f * in[c]);
        }
    }
    return json::object();
}

static json handle(const std::string &method, const json &data) {
    if (method == "describe_effect_v1")
        return describe();
    if (method == "query_vram_requirement_v1")
        return {{"min_mb", 0}, {"max_mb", 0}};
    if (method == "set_vram_limit_v1")
        return json::object();
    if (method == "run_generate_v1")
        return run_generate(data);
    throw std::runtime_error("Unknown method " + method);
}

int main() {
    const char *url = std::getenv("FLEXI_SERVER_URL");
    if (!url) {
        std::fprintf(stderr, "FLEXI_SERVER_URL is not set: Flexi effects are launched by the host application.\n");
        return 1;
    }
    std::signal(SIGPIPE, SIG_IGN);
    try {
        WebSocket ws(url);
        for (;;) {
            json parsed = json::parse(ws.receive());
            std::vector<json> messages = parsed.is_array() ? parsed.get<std::vector<json>>() : std::vector<json>{parsed};
            for (const json &message : messages) {
                std::string method = message.value("method", "");
                std::string upper = method;
                std::transform(upper.begin(), upper.end(), upper.begin(), [](unsigned char c) { return std::toupper(c); });
                json reply = {{"effect", message.value("effect", json())}, {"method", upper}, {"id", message.value("id", json())}};
                if (method == "shutdown_v1") {
                    reply["data"] = json::object();
                    ws.send(reply.dump());
                    ws.close();
                    return 0;
                }
                try {
                    const json &effect = message.at("effect");
                    if (effect.at(0) != IDENTIFIER || effect.at(1) != VERSION)
                        throw std::runtime_error("Unregistered effect " + effect.dump());
                    reply["data"] = handle(method, message.value("data", json::object()));
                } catch (const std::exception &e) {
                    reply["log"] = json::array({{{"level", 3}, {"message", e.what()}, {"detail", ""}}});
                }
                ws.send(reply.dump());
            }
        }
    } catch (const Closed &) {
        return 0;
    } catch (const std::exception &e) {
        std::fprintf(stderr, "flexi_invert: %s\n", e.what());
        return 1;
    }
}
