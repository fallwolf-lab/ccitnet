import time
import requests


def rc4_encrypt(key: str, plaintext: str) -> str:
    """RC4 加密，返回十六进制字符串"""
    key_bytes = key.encode()
    plain_bytes = plaintext.encode()

    # KSA (Key Scheduling Algorithm)
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key_bytes[i % len(key_bytes)]) % 256
        s[i], s[j] = s[j], s[i]

    # PRGA (Pseudo-Random Generation Algorithm)
    i = j = 0
    cipher = []
    for byte in plain_bytes:
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        k = s[(s[i] + s[j]) % 256]
        cipher.append(byte ^ k)

    return bytes(cipher).hex()



#TODO 请在登录函数中修改您的账号和密码
def login() -> bool:
    url = "http://1.1.1.4/ac_portal/login.php"
    timestamp = str(int(time.time() * 1000))  # 13位时间戳

    data = {
        "opr": "pwdLogin",
        "userName": "您的账号",
        "pwd": rc4_encrypt(timestamp, "您的密码"),
        "auth_tag": timestamp,
        "rememberPwd": "0",
    }

    try:
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code == 200:
            print(f"登录成功！状态码: {resp.status_code}")
            return True
        else:
            print(f"登录失败，状态码: {resp.status_code}")
            print(f"响应内容: {resp.text[:500]}")
            return False
    except requests.RequestException as e:
        print(f"请求异常: {e}")
        return False


if __name__ == "__main__":
    login()
