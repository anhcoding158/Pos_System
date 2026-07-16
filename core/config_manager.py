import json
import os


class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config_data = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            default_config = {
                "store_info": {
                    "name": "TÊN QUÁN CỦA KHÁCH HÀNG",
                    "address": "Địa chỉ quán",
                    "phone": "0999.888.777"
                },
                "hardware": {
                    "printer_name": "Microsoft Print to PDF",
                    "paper_size": "K80"
                },
                "security": {
                    "mac_address": "",
                    "is_activated": False
                }
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            return default_config

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Lỗi đọc file cấu hình: {e}")
            return {}

    def get(self, section, key):
        return self.config_data.get(section, {}).get(key, "")

    def update(self, section, key, value):
        if section not in self.config_data:
            self.config_data[section] = {}

        self.config_data[section][key] = value

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Lỗi khi lưu cấu hình: {e}")
            return False
