"""Guard aktivasi yang menghentikan jalur bot dan billing sebelum dijalankan."""

def activation_java_guard(account_expression: str = "account") -> str:
    return f'''\n        if (!TeleBetaFreemium.isActive({account_expression})) {{\n            if (!TeleBetaFreemium.activate({account_expression})) return;\n        }}\n        return;\n'''
