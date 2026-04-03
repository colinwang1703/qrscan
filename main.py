import cv2
from pyzbar.pyzbar import decode
import time
import webbrowser
import os
from datetime import datetime

LOG_FILE = "scan_log.txt"
TIMEOUT_SECONDS = 30
recent_qrs = {}

def is_url(text):
    """简单判断是否是以 http 或 https 开头的链接"""
    return text.lower().startswith(('http://', 'https://'))

def log_qr(content):
    """记录扫到的二维码到文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {content}\n")
    print(f"[{timestamp}] 扫码成功并记录: {content}")

def main():
    print("正在启动摄像头...")
    # 尝试多种组合寻找可用的摄像头
    cap = None
    for index in [0, 1]:
        for backend in [cv2.CAP_ANY, cv2.CAP_DSHOW, cv2.CAP_MSMF]:
            c = cv2.VideoCapture(index, backend)
            if c.isOpened():
                ret, _ = c.read()
                if ret:
                    cap = c
                    print(f"成功打开摄像头 (Index: {index}, Backend: {backend})")
                    break
                else:
                    c.release()
            else:
                c.release()
        if cap is not None:
            break
            
    if cap is None or not cap.isOpened():
        print("无法打开摄像头！")
        print("排查建议：")
        print("1. 请进入Windows的“设置” -> “隐私和安全性” -> “相机”，确保“允许应用访问你的相机”选项已开启。")
        print("2. 确保没有其他应用（如微信、OBS、浏览器等）正在使用摄像头。")
        print("3. 如果使用外接摄像头，请检查USB连接。")
        return

    print("摄像头已启动！对准二维码即可扫描。在视频窗口按 'q' 键退出程序。")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法获取摄像头画面...")
            time.sleep(1)
            continue

        # 识别当前帧中的所有二维码
        decoded_objects = decode(frame)
        current_time = time.time()

        for obj in decoded_objects:
            # 提取二维码内容
            qr_content = obj.data.decode('utf-8')
            
            # 检查这个二维码最近是否出现过
            last_seen = recent_qrs.get(qr_content, 0)
            if current_time - last_seen > TIMEOUT_SECONDS:
                # 记录为最近30秒内出现过
                recent_qrs[qr_content] = current_time
                
                # 记录到文件
                log_qr(qr_content)
                
                # 如果是网页链接，则在默认浏览器打开
                if is_url(qr_content):
                    print(f"----> 检测到网页链接，正在打开: {qr_content}")
                    webbrowser.open(qr_content)

        # 实时显示画面，方便用户对准二维码
        cv2.imshow("QR Code Scanner", frame)
        
        # 捕捉按键，如果是 'q' 则退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("停止扫描，退出程序。")
            break

    # 释放资源
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
