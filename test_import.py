import traceback

try:
    import media_organizer

    print("Module imported successfully")

    # Try to run the main function if it exists
    if hasattr(media_organizer, "main"):
        media_organizer.main()
    else:
        print("No main function found, trying to create GUI")
        import tkinter as tk

        root = tk.Tk()
        app = media_organizer.MediaOrganizerGUI(root)
        root.mainloop()

except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
