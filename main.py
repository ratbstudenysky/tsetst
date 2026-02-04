import time
import requests
import pyautogui
import io
import keyboard
import threading
import tkinter as tk
from datetime import datetime
import google.generativeai as genai
from PIL import Image
import winsound

# ==========================================
# ⚙️ ส่วนตั้งค่า (Configuration)
# ==========================================

# 1. Discord Webhook URL
WEBHOOK_URL = "YOUR_WEBHOOK_URL_HERE"

# 2. Google Gemini API Key (ใส่ Key ที่คุณให้มา)
GEMINI_API_KEY = "YOUR_API_KEY" 

# 3. Model Name (ใช้ 2.5 Flash ตามที่ขอ)
# ตัวเลือก: 'gemini-2.5-flash' (Stable), 'gemini-3-flash-preview' (Newer)
MODEL_NAME = "gemini-2.5-flash" 

# 4. ปุ่ม Trigger
TRIGGER_KEY = "f9"

# 5. เปิดเสียง Beep เมื่อกดหรือไม่
PLAY_SOUND = True

# ==========================================
# 🤖 ตั้งค่า AI
# ==========================================
try:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Config ให้ตอบสั้น กระชับ ตรงประเด็น
    generation_config = {
        "temperature": 0.1, # ลดความมั่ว เน้นความแม่น
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 100, # จำกัดคำตอบไม่ให้ยาวเกินไป
    }
    
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config
    )
    print(f"✅ AI Model Loaded: {MODEL_NAME}")
except Exception as e:
    print(f"❌ Error Loading AI: {e}")

# ==========================================
# 🖥️ ส่วน Popup แจ้งเตือน (Stealth UI)
# ==========================================
def show_stealth_popup(text, duration=2000):
    """
    แสดง Popup ไร้ขอบที่มุมขวาล่าง 2 วินาที โดยไม่แย่ง Focus
    """
    def run_popup():
        try:
            root = tk.Tk()
            root.overrideredirect(True) # ปิดขอบหน้าต่าง (Title bar)
            root.attributes('-topmost', True) # อยู่บนสุดเสมอ
            root.attributes('-alpha', 0.85) # โปร่งใสเล็กน้อย (ให้ดู Hi-tech/เนียน)
            root.configure(bg='black')

            # ตั้งค่าฟอนต์และข้อความ
            label = tk.Label(
                root, 
                text=text, 
                fg='#00ff00', # สีเขียว Hacker
                bg='black', 
                font=("Segoe UI", 12, "bold"),
                wraplength=350,
                padx=10, 
                pady=5
            )
            label.pack()

            # คำนวณตำแหน่ง (มุมขวาล่าง เหนือ Taskbar)
            root.update_idletasks()
            width = label.winfo_reqwidth() + 20
            height = label.winfo_reqheight() + 10
            
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            x_pos = screen_width - width - 20
            y_pos = screen_height - height - 50 # เว้นที่ให้ Taskbar นิดหน่อย
            
            root.geometry(f'{width}x{height}+{x_pos}+{y_pos}')

            # ตั้งเวลาปิดตัวเอง
            root.after(duration, root.destroy)
            root.mainloop()
        except Exception as e:
            print(f"Popup Error: {e}")

    # รัน Popup ใน Thread แยกเพื่อไม่ให้โปรแกรมหลักค้าง
    threading.Thread(target=run_popup).start()

# ==========================================
# 🧠 AI Logic
# ==========================================
def get_ai_analysis(image_obj):
    try:
        # Prompt สั่งให้ตอบสั้นที่สุดเพื่อขึ้น Popup ได้สวยๆ
        prompt = """
        Analyze this exam question/image.
        Output ONLY the correct answer. 
        Keep it extremely short (under 10 words).
        Example format: "Answer: B (Mitochondria)" or "x = 5"
        If no question, say "No Question".
        Language: Thai or English (Match context).
        """
        
        response = model.generate_content([prompt, image_obj])
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def task_process():
    try:
        start_time = time.time()
        
        # 1. จับภาพ (เงียบ)
        screenshot = pyautogui.screenshot()
        
        # 2. ให้ AI คิด
        # แปลงรูปเป็น Bytes ให้ AI ก่อน (บางครั้งส่ง object ตรงๆ อาจช้ากว่า)
        ai_answer = "Analyzing..."
        try:
            ai_answer = get_ai_analysis(screenshot)
        except Exception as e:
            ai_answer = "AI Fail"

        # 3. 🔥 แสดง Popup ทันทีที่ได้คำตอบ!
        print(f"AI Answer: {ai_answer}")
        show_stealth_popup(ai_answer, duration=2500) # โชว์ 2.5 วินาที

        # 4. ส่งเข้า Discord (ทำทีหลังได้ ไม่รีบ)
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='JPEG', quality=70) # ลด quality นิดหน่อยให้ส่งไว
        img_byte_arr.seek(0)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        filename = f"solved_{datetime.now().strftime('%H%M%S')}.jpg"
        
        discord_msg = f"⚡ **{ai_answer}**\n`{MODEL_NAME}` | ⏱️ {timestamp}"
        
        files = {'file': (filename, img_byte_arr, 'image/jpeg')}
        payload = {"content": discord_msg}
        
        if "YOUR_WEBHOOK" not in WEBHOOK_URL:
             requests.post(WEBHOOK_URL, data=payload, files=files)

    except Exception as e:
        print(f"Process Error: {e}")

def on_key_press():
    # เสียงติ๊ดสั้นๆ (ยืนยันว่ากดติด)
    if PLAY_SOUND:
        threading.Thread(target=lambda: winsound.Beep(1500, 50)).start()
    
    # เริ่มกระบวนการคิด
    threading.Thread(target=task_process).start()

def main():
    print(f"--- Gemini 2.5 Flash Stealth Helper ---")
    print(f"Model: {MODEL_NAME}")
    print(f"Ready. Press '{TRIGGER_KEY}' to solve.")
    print("Popup will appear at bottom-right.")
    
    if "YOUR_API_KEY" in GEMINI_API_KEY:
        print("\n⚠️  WARNING: กรุณาใส่ API Key ในบรรทัดที่ 21")
        return

    # Global Hook (ทำงานแม้พับจอ)
    keyboard.add_hotkey(TRIGGER_KEY, on_key_press, suppress=False)
    keyboard.wait()

if __name__ == "__main__":
    main()
