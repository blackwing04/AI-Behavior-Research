"""
Streamlit UI 應用打包為 .exe 的工具
執行此腳本將生成獨立的 .exe 檔案（~600MB）
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

def build_exe():
    """打包 Streamlit 應用為 .exe"""
    
    project_root = Path(__file__).parent
    ui_app = project_root / "ui_app.py"
    build_dir = project_root / "build_pyinstaller"
    dist_dir = project_root / "dist"
    
    print("=" * 70)
    print(" 開始打包 Streamlit 應用為 .exe...")
    print("=" * 70)
    print(f"\n 專案目錄：{project_root}")
    print(f" 輸出目錄：{dist_dir}")
    
    # 檢查 ui_app.py 是否存在
    if not ui_app.exists():
        print(f" 找不到 {ui_app}")
        return False
    
    # 清理舊的打包檔案
    print("\n 清理舊的打包檔案...")
    for d in [build_dir, dist_dir]:
        if d.exists():
            try:
                shutil.rmtree(d)
                print(f"    已刪除 {d.name}")
            except:
                pass
    
    # 確保 PyInstaller 已安裝
    print("\n 檢查 PyInstaller...")
    try:
        import PyInstaller
        print("    PyInstaller 已安裝")
    except ImportError:
        print("   ️ 安裝 PyInstaller...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "-q"])
        if result.returncode != 0:
            print(" PyInstaller 安裝失敗")
            return False
    
    # PyInstaller 命令（簡化配置避免依賴問題）
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",                                    # 打包成單一 .exe
        "--name", "AI-Behavior-UI",                    # 執行檔名稱
        "--distpath", str(dist_dir),                   # 輸出目錄
        "--workpath", str(build_dir / "build"),       # 工作目錄
        "--specpath", str(build_dir),                 # spec 檔目錄
        "--collect-all=streamlit",                    # 自動收集 streamlit 所有資源
        "--collect-all=altair",
        "--collect-all=pandas",
        "--exclude-module=pyarrow",                    # 排除 pyarrow（造成問題）
        "--exclude-module=tests",
        "--exclude-module=pytest",
        "-y",                                          # 覆蓋不詢問
        str(ui_app)
    ]
    
    print(f"\n 開始打包（這會花費幾分鐘，請耐心等候...）")
    print(f"   PyInstaller 正在編譯和打包中...")
    
    try:
        result = subprocess.run(cmd, cwd=str(project_root), capture_output=False)
        
        if result.returncode == 0:
            exe_path = dist_dir / "AI-Behavior-UI.exe"
            if exe_path.exists():
                file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
                print("\n" + "=" * 70)
                print(" 打包完成！")
                print("=" * 70)
                print(f"\n 執行檔位置：{exe_path}")
                print(f" 檔案大小：{file_size:.1f} MB")
                print(f"\n 使用方式：")
                print(f"    直接雙擊 {exe_path.name} 執行")
                print(f"    或在命令列執行：{exe_path}")
                print(f"\n️  重要提示：")
                print(f"    第一次執行會較慢（15-30秒，Streamlit 初始化）")
                print(f"    應用會自動在預設瀏覽器開啟")
                print(f"    瀏覽器會顯示 http://localhost:8501")
                print(f"    按 Ctrl+C 停止應用")
                print(f"\n 打包暫存檔：{build_dir}（可刪除）")
                return True
            else:
                print(" 打包失敗：找不到輸出檔案")
                return False
        else:
            print(" 打包失敗，請檢查上面的錯誤訊息")
            return False
            
    except Exception as e:
        print(f" 錯誤：{e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = build_exe()
    input("\n按 Enter 鍵結束...")
    sys.exit(0 if success else 1)
