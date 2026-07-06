"""Character identity: name, GUID, game mode."""
import customtkinter as ctk

from core import character


class CharacterPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        sf = self.app.save
        if sf is None:
            return
        form = ctk.CTkFrame(self, corner_radius=10)
        form.pack(fill="x", pady=8)
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Name").grid(
            row=0, column=0, sticky="w", padx=14, pady=(14, 4))
        self.name_var = ctk.StringVar(value=character.get_name(sf.data))
        ctk.CTkEntry(form, textvariable=self.name_var).grid(
            row=0, column=1, sticky="ew", padx=(0, 14), pady=(14, 4))

        ctk.CTkLabel(form, text="GUID").grid(
            row=1, column=0, sticky="w", padx=14, pady=4)
        self.guid_var = ctk.StringVar(value=character.get_guid(sf.data))
        ctk.CTkEntry(form, textvariable=self.guid_var).grid(
            row=1, column=1, sticky="ew", padx=(0, 14), pady=4)
        ctk.CTkButton(form, text="Randomize", width=100,
                      command=lambda: self.guid_var.set(
                          character.random_guid())
                      ).grid(row=1, column=2, padx=(0, 14), pady=4)

        ctk.CTkLabel(form, text="Mode").grid(
            row=2, column=0, sticky="w", padx=14, pady=4)
        self.mode_var = ctk.StringVar(value=character.get_mode(sf.data))
        ctk.CTkOptionMenu(form, variable=self.mode_var,
                          values=list(character.MODE_OPTIONS)
                          ).grid(row=2, column=1, sticky="w",
                                 padx=(0, 14), pady=4)

        ctk.CTkButton(form, text="Apply", width=120, command=self._apply
                      ).grid(row=3, column=1, sticky="w", pady=(10, 14))
        ctk.CTkLabel(
            self,
            text="Changing name or mode gives the character a new GUID, so "
                 "the game treats it as a separate character.",
            text_color=("gray40", "gray60"), wraplength=560, justify="left"
        ).pack(anchor="w", pady=(6, 0))

    def _apply(self):
        try:
            written = character.set_identity(
                self.app.save, self.name_var.get(),
                self.guid_var.get(), self.mode_var.get())
        except ValueError as e:
            self.app.set_status(str(e))
            return
        self.guid_var.set(written)
        self.app.mark_dirty()
        self.app.set_status("Character updated — press Save to keep.")
        self.refresh()
