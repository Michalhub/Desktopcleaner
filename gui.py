import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import icons_manager as im

class IconLayoutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🖥️ DesktopCleaner – układy ikon")

        tk.Label(root, text="Wybierz profil układu:").pack(pady=5)

        self.profiles = im.list_profiles()
        self.profile_var = tk.StringVar()
        self.profile_var.set(self.profiles[0] if self.profiles else "")

        if self.profiles:
            self.dropdown = tk.OptionMenu(root, self.profile_var, *self.profiles)
        else:
            self.dropdown = tk.OptionMenu(root, self.profile_var, "")
        self.dropdown.pack(pady=5)

        tk.Button(root, text="💾 Zapisz nowy układ", command=self.save_layout).pack(pady=5)
        tk.Button(root, text="🔁 Przywróć wybrany układ", command=self.restore_layout).pack(pady=5)
        tk.Button(root, text="🗑️ Usuń profil", command=self.delete_profile).pack(pady=5)
        tk.Button(root, text="🔄 Odśwież listę profili", command=self.refresh_profiles).pack(pady=5)

    def refresh_profiles(self):
        self.profiles = im.list_profiles()
        menu = self.dropdown["menu"]
        menu.delete(0, "end")
        for p in self.profiles:
            menu.add_command(label=p, command=lambda v=p: self.profile_var.set(v))
        self.profile_var.set(self.profiles[0] if self.profiles else "")

    def save_layout(self):
        profile = simpledialog.askstring("Zapisz układ", "Podaj nazwę profilu:")
        if profile:
            try:
                im.save_layout(profile)
                messagebox.showinfo("Sukces", f"Układ zapisany jako '{profile}'.")
                self.refresh_profiles()
            except Exception as e:
                messagebox.showerror("Błąd", str(e))

    def restore_layout(self):
        profile = self.profile_var.get()
        if not profile:
            messagebox.showwarning("Brak wyboru", "Wybierz profil z listy.")
            return
        try:
            im.restore_layout(profile)
            messagebox.showinfo("Sukces", f"Układ '{profile}' został przywrócony.")
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def delete_profile(self):
        profile = self.profile_var.get()
        if not profile:
            messagebox.showwarning("Brak profilu", "Wybierz profil do usunięcia.")
            return
        if messagebox.askyesno("Usuń profil", f"Czy na pewno usunąć profil '{profile}'?"):
            try:
                path = os.path.join("layouts", f"layout_{profile}.pkl")
                if os.path.exists(path):
                    os.remove(path)
                    messagebox.showinfo("Usunięto", f"Profil '{profile}' został usunięty.")
                    self.refresh_profiles()
                else:
                    messagebox.showwarning("Nie znaleziono", "Plik profilu nie istnieje.")
            except Exception as e:
                messagebox.showerror("Błąd", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = IconLayoutApp(root)
    root.mainloop()