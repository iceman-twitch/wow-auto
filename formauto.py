# -*- coding: utf-8 -*-
"""
FormAuto - GUI for WoW Automation (Backward compatibility wrapper)

This file is maintained for backward compatibility.
For new code, use: from formauto import SettingsForm
"""

from formauto import SettingsForm

# Re-export for backward compatibility
__all__ = ["SettingsForm"]


if __name__ == "__main__":
    app = SettingsForm()
    app.mainloop()
