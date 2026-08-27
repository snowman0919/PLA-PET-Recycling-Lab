#include "protocol.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace recycler {

uint16_t crc16_ccitt(const uint8_t* data, size_t length) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < length; ++i) {
    crc ^= static_cast<uint16_t>(data[i]) << 8;
    for (uint8_t bit = 0; bit < 8; ++bit) {
      crc = (crc & 0x8000U) ? static_cast<uint16_t>((crc << 1) ^ 0x1021U)
                            : static_cast<uint16_t>(crc << 1);
    }
  }
  return crc;
}

namespace {
bool copy_field(char* destination, size_t capacity, const char* start, size_t length) {
  if (length >= capacity) return false;
  memcpy(destination, start, length);
  destination[length] = '\0';
  return true;
}

bool parse_hex4(const char* value, uint16_t* result) {
  if (strlen(value) != 4) return false;
  char* end = nullptr;
  const unsigned long parsed = strtoul(value, &end, 16);
  if (end != value + 4 || parsed > 0xFFFFUL) return false;
  *result = static_cast<uint16_t>(parsed);
  return true;
}
}  // namespace

ProtocolStatus decode_frame(const char* line, size_t length, ProtocolFrame* out) {
  if (length == 0 || length >= kMaximumFrameBytes) return ProtocolStatus::TOO_LONG;
  while (length > 0 && (line[length - 1] == '\n' || line[length - 1] == '\r')) --length;

  const char* separators[4] = {nullptr, nullptr, nullptr, nullptr};
  size_t separator_count = 0;
  for (size_t i = 0; i < length; ++i) {
    if (line[i] == '|') {
      if (separator_count >= 4) return ProtocolStatus::BAD_FIELD_COUNT;
      separators[separator_count++] = line + i;
    }
  }
  if (separator_count != 4) return ProtocolStatus::BAD_FIELD_COUNT;
  if (static_cast<size_t>(separators[0] - line) != 4 || memcmp(line, "FRP1", 4) != 0)
    return ProtocolStatus::BAD_VERSION;

  const char* type_start = separators[0] + 1;
  const char* sequence_start = separators[1] + 1;
  const char* payload_start = separators[2] + 1;
  const char* crc_start = separators[3] + 1;
  if (!copy_field(out->type, sizeof(out->type), type_start,
                  static_cast<size_t>(separators[1] - type_start)) ||
      !copy_field(out->payload, sizeof(out->payload), payload_start,
                  static_cast<size_t>(separators[3] - payload_start))) {
    return ProtocolStatus::FIELD_TOO_LONG;
  }

  char sequence_text[12];
  if (!copy_field(sequence_text, sizeof(sequence_text), sequence_start,
                  static_cast<size_t>(separators[2] - sequence_start)))
    return ProtocolStatus::BAD_SEQUENCE;
  char* end = nullptr;
  const unsigned long sequence = strtoul(sequence_text, &end, 10);
  if (*sequence_text == '\0' || *end != '\0' || sequence > 0xFFFFFFFFUL)
    return ProtocolStatus::BAD_SEQUENCE;

  char crc_text[5];
  if (!copy_field(crc_text, sizeof(crc_text), crc_start,
                  static_cast<size_t>(line + length - crc_start)))
    return ProtocolStatus::BAD_CRC;
  uint16_t transmitted_crc = 0;
  if (!parse_hex4(crc_text, &transmitted_crc)) return ProtocolStatus::BAD_CRC;
  const size_t protected_length = static_cast<size_t>(separators[3] - line);
  if (crc16_ccitt(reinterpret_cast<const uint8_t*>(line), protected_length) !=
      transmitted_crc)
    return ProtocolStatus::BAD_CRC;

  out->sequence = static_cast<uint32_t>(sequence);
  return ProtocolStatus::OK;
}

bool sequence_is_newer(uint32_t candidate, uint32_t previous) {
  return candidate != previous && static_cast<int32_t>(candidate - previous) > 0;
}

size_t encode_frame(char* output, size_t capacity, const char* type,
                    uint32_t sequence, const char* payload) {
  if (!output || !type || !payload || capacity == 0 || strchr(type, '|') ||
      strchr(payload, '|') || strchr(type, '\n') || strchr(payload, '\n'))
    return 0;
  const int prefix = snprintf(output, capacity, "FRP1|%s|%lu|%s", type,
                              static_cast<unsigned long>(sequence), payload);
  if (prefix < 0 || static_cast<size_t>(prefix) + 6 > capacity) return 0;
  const uint16_t crc = crc16_ccitt(reinterpret_cast<const uint8_t*>(output),
                                  static_cast<size_t>(prefix));
  const int suffix = snprintf(output + prefix, capacity - static_cast<size_t>(prefix),
                              "|%04X\n", crc);
  if (suffix != 6) return 0;
  return static_cast<size_t>(prefix + suffix);
}

}  // namespace recycler
