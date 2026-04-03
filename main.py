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

    print("摄像头已启动！目前运行在“无窗口低性能消耗”模式。")
    print("请将二维码对准摄像头扫描... （在终端中按 Ctrl+C 退出程序）")

    last_decode_time = 0
    DECODE_INTERVAL = 0.5  # 限制解码频率：每 0.5 秒解码一次，大幅降低 CPU 占用

    try:
        while True:
            # 持续抓取画面，用于清空摄像头底层缓冲，保持画面是最新的
            if not cap.grab():
                print("等待摄像头画面...")
                time.sleep(0.5)
                continue

            current_time = time.time()
            # 每隔指定时间，才进行高能耗的“获取真实像素+二维码解码”操作
            if current_time - last_decode_time >= DECODE_INTERVAL:
                ret, frame = cap.retrieve()
                if not ret:
                    continue

                # 识别当前帧中的所有二维码
                decoded_objects = decode(frame)
                last_decode_time = current_time

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
    except KeyboardInterrupt:
        print("\n收到退出指令，停止扫描，退出程序。")
    finally:
        # 释放资源
        cap.release()

if __name__ == "__main__":
    main()
