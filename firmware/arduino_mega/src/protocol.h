#pragma once

#include <stddef.h>
#include <stdint.h>

namespace recycler {

constexpr size_t kMaximumFrameBytes = 160;

enum class ProtocolStatus : uint8_t {
  OK,
  TOO_LONG,
  BAD_FIELD_COUNT,
  BAD_VERSION,
  BAD_SEQUENCE,
  BAD_CRC,
  FIELD_TOO_LONG,
};

struct ProtocolFrame {
  uint32_t sequence;
  char type[16];
  char payload[96];
};

uint16_t crc16_ccitt(const uint8_t* data, size_t length);
ProtocolStatus decode_frame(const char* line, size_t length, ProtocolFrame* out);
bool sequence_is_newer(uint32_t candidate, uint32_t previous);
size_t encode_frame(char* output, size_t capacity, const char* type,
                    uint32_t sequence, const char* payload);

}  // namespace recycler
