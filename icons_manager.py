import os
import pickle
import win32gui
import ctypes

# 📁 Folder do zapisu układów ikon
LAYOUTS_FOLDER = "layouts"

# 🔧 Stałe Windows API
LVM_GETITEMCOUNT    = 0x1004
LVM_GETITEMPOSITION = 0x1010
LVM_GETITEMTEXTW    = 0x1073
LVM_SETITEMPOSITION = 0x100F
LVIF_TEXT = 0x0001

# 🧱 Struktura LVITEMW
class LVITEMW(ctypes.Structure):
    _fields_ = [
        ("mask", ctypes.c_uint),
        ("iItem", ctypes.c_int),
        ("iSubItem", ctypes.c_int),
        ("state", ctypes.c_uint),
        ("stateMask", ctypes.c_uint),
        ("pszText", ctypes.c_void_p),
        ("cchTextMax", ctypes.c_int),
        ("iImage", ctypes.c_int),
        ("lParam", ctypes.c_long),
        ("iIndent", ctypes.c_int),
        ("iGroupId", ctypes.c_int),
        ("cColumns", ctypes.c_uint),
        ("puColumns", ctypes.POINTER(ctypes.c_uint)),
        ("piColFmt", ctypes.POINTER(ctypes.c_int)),
        ("iGroup", ctypes.c_int),
    ]

# 📌 Znajdowanie uchwytu do listy ikon pulpitu
def get_desktop_listview():
    defview = []

    def enum_windows_callback(hwnd, lParam):
        class_name = win32gui.GetClassName(hwnd)
        if class_name == "SHELLDLL_DefView":
            defview.append(hwnd)
            return False
        return True

    progman = win32gui.FindWindow("Progman", None)
    win32gui.EnumChildWindows(progman, enum_windows_callback, None)

    if not defview:
        def find_workerw():
            result = []
            def enum_worker(hwnd, lParam):
                class_name = win32gui.GetClassName(hwnd)
                if class_name == "WorkerW":
                    child = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
                    if child:
                        result.append(child)
                return True
            win32gui.EnumWindows(enum_worker, None)
            return result[0] if result else None

        defview_hwnd = find_workerw()
    else:
        defview_hwnd = defview[0]

    if not defview_hwnd:
        print("❌ Nie znaleziono SHELLDLL_DefView")
        return None

    listview = win32gui.FindWindowEx(defview_hwnd, 0, "SysListView32", "FolderView")
    if not listview:
        print("❌ Nie znaleziono SysListView32")
    return listview

# 📥 Pobieranie pozycji ikon (z filtrem pustych nazw)
def get_icon_positions():
    hwnd = get_desktop_listview()
    if not hwnd:
        raise Exception("❌ Nie znaleziono listy ikon.")

    count = win32gui.SendMessage(hwnd, LVM_GETITEMCOUNT, 0, 0)
    print(f"🔎 Znaleziono {count} ikon.")

    positions = {}

    for i in range(count):
        buf = ctypes.create_string_buffer(8)
        win32gui.SendMessage(hwnd, LVM_GETITEMPOSITION, i, ctypes.addressof(buf))
        x, y = ctypes.cast(buf, ctypes.POINTER(ctypes.c_long * 2)).contents

        buffer = ctypes.create_unicode_buffer(260)
        item = LVITEMW()
        item.mask = LVIF_TEXT
        item.iItem = i
        item.iSubItem = 0
        item.pszText = ctypes.cast(buffer, ctypes.c_void_p)
        item.cchTextMax = 260

        try:
            win32gui.SendMessage(hwnd, LVM_GETITEMTEXTW, i, ctypes.cast(ctypes.pointer(item), ctypes.c_void_p))
            name = buffer.value.strip()

            if name:
                positions[name] = (x, y)
                print(f"🧩 Ikona {i}: '{name}' @ ({x},{y})")
            else:
                print(f"⚠️ Pominięto pustą ikonę #{i} @ ({x},{y})")

        except Exception as e:
            print(f"⚠️ Błąd przy ikonie {i}: {e}")

    return positions

# ♻️ Przywracanie pozycji ikon
def set_icon_positions(saved_positions):
    hwnd = get_desktop_listview()
    if not hwnd:
        raise Exception("❌ Nie znaleziono listy ikon.")

    count = win32gui.SendMessage(hwnd, LVM_GETITEMCOUNT, 0, 0)
    print(f"🔁 Przywracanie {count} ikon.")

    for i in range(count):
        buffer = ctypes.create_unicode_buffer(260)
        item = LVITEMW()
        item.mask = LVIF_TEXT
        item.iItem = i
        item.iSubItem = 0
        item.pszText = ctypes.cast(buffer, ctypes.c_void_p)
        item.cchTextMax = 260

        try:
            win32gui.SendMessage(hwnd, LVM_GETITEMTEXTW, i, ctypes.cast(ctypes.pointer(item), ctypes.c_void_p))
            name = buffer.value.strip()

            if name in saved_positions:
                x, y = saved_positions[name]
                lparam = x | (y << 16)
                print(f"✅ Ustawiam '{name}' na ({x},{y})")
                win32gui.SendMessage(hwnd, LVM_SETITEMPOSITION, i, lparam)
            else:
                print(f"⚠️ Ikona '{name}' nie ma zapisanej pozycji.")

        except Exception as e:
            print(f"❌ Błąd przy ustawianiu pozycji {i}: {e}")

# 💾 Zapis profilu
def save_layout(profile_name):
    os.makedirs(LAYOUTS_FOLDER, exist_ok=True)
    positions = get_icon_positions()
    file_path = os.path.join(LAYOUTS_FOLDER, f"layout_{profile_name}.pkl")
    with open(file_path, 'wb') as f:
        pickle.dump(positions, f)
    print(f"✅ Układ '{profile_name}' zapisany.")
    return file_path

# 🔁 Przywrócenie profilu
def restore_layout(profile_name):
    file_path = os.path.join(LAYOUTS_FOLDER, f"layout_{profile_name}.pkl")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ Nie znaleziono profilu: {profile_name}")
    with open(file_path, 'rb') as f:
        positions = pickle.load(f)
    print(f"📂 Wczytano {len(positions)} ikon z profilu '{profile_name}'")
    set_icon_positions(positions)

# 📃 Lista dostępnych profili
def list_profiles():
    if not os.path.exists(LAYOUTS_FOLDER):
        return []
    return [f.replace("layout_", "").replace(".pkl", "") for f in os.listdir(LAYOUTS_FOLDER) if f.endswith(".pkl")]
