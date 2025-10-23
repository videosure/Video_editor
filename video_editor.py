import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import sys
import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip

# --- NEW DIAGNOSTIC CODE ---
# Print debug information to the console *before* trying any imports
print("--- Python Debug Information ---")
print(f"Script running with Python executable:\n{sys.executable}\n")
print("Python will search for libraries in these paths (sys.path):")
for path in sys.path:
    print(f"  - {path}")
print("----------------------------------\n")
# --- END DIAGNOSTIC CODE ---


# --- MoviePy Check ---
# We must check for moviepy before proceeding, as it's the core engine.
try:
    from moviepy import (
        VideoFileClip, 
        AudioFileClip, 
        concatenate_videoclips,
        CompositeVideoClip
    )
except ImportError:
    # If moviepy isn't installed, we can't run.
    # We'll show this error in the console.
    print("ERROR: The 'moviepy' library is not found.")
    print("Please install it to run this application:")
    print("  pip install moviepy")
    # We can also try to show a graphical popup, but if tkinter fails,
    # the console print is the fallback.
    try:
        root = tk.Tk()
        root.withdraw() # Hide the main window
        messagebox.showerror(
            "Missing Library",
            "The 'moviepy' library is not found.\nPlease install it to run this application:\n\npip install moviepy"
        )
    except tk.TclError:
        pass # Failed to create Tk root, console print will have to do.
    sys.exit(1) # Exit the script


class VideoEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Video Editor")
        self.root.geometry("600x500") # Set a reasonable default size

        # --- Data Storage ---
        self.video_clips = [] # List to store paths to video clips
        self.music_file = None # Path to the music file

        # --- Styling ---
        style = ttk.Style()
        style.theme_use('clam') # Use a modern theme
        style.configure('TButton', padding=6, relief="flat", font=('Helvetica', 10))
        style.configure('TLabel', font=('Helvetica', 10))
        style.configure('TFrame', padding=10)
        style.configure('TLabelFrame', padding=10, font=('Helvetica', 11, 'bold'))

        # --- Main Frame ---
        main_frame = ttk.Frame(root, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Make the main frame's grid responsive
        main_frame.rowconfigure(0, weight=3) # Video listbox gets more space
        main_frame.rowconfigure(1, weight=1) # Music frame
        main_frame.rowconfigure(2, weight=1) # Export frame
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=0) # Button column

        # --- 1. Video Clips Section ---
        video_frame = ttk.LabelFrame(main_frame, text="1. Add Video Clips (in order)")
        video_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        video_frame.rowconfigure(0, weight=1)
        video_frame.columnconfigure(0, weight=1)
        video_frame.columnconfigure(1, weight=0)
        
        # Listbox to show video clips
        self.video_listbox = tk.Listbox(video_frame, height=10, selectmode=tk.SINGLE, borderwidth=1, relief="solid")
        self.video_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Scrollbar for the listbox
        scrollbar = ttk.Scrollbar(video_frame, orient=tk.VERTICAL, command=self.video_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.video_listbox.config(yscrollcommand=scrollbar.set)

        # Button frame for video actions
        video_buttons_frame = ttk.Frame(video_frame)
        video_buttons_frame.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.add_video_btn = ttk.Button(video_buttons_frame, text="Add Clip(s)", command=self.add_video_clips)
        self.add_video_btn.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        self.remove_video_btn = ttk.Button(video_buttons_frame, text="Remove Selected", command=self.remove_video_clip)
        self.remove_video_btn.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        self.move_up_btn = ttk.Button(video_buttons_frame, text="Move Up", command=self.move_clip_up)
        self.move_up_btn.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        self.move_down_btn = ttk.Button(video_buttons_frame, text="Move Down", command=self.move_clip_down)
        self.move_down_btn.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)


        # --- 2. Music Section ---
        music_frame = ttk.LabelFrame(main_frame, text="2. Add Music (Optional)")
        music_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        music_frame.columnconfigure(0, weight=1)

        self.music_label = ttk.Label(music_frame, text="No music selected.", anchor="w", relief="solid", padding=5)
        self.music_label.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.add_music_btn = ttk.Button(music_frame, text="Add Music", command=self.add_music)
        self.add_music_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.remove_music_btn = ttk.Button(music_frame, text="Remove", command=self.remove_music)
        self.remove_music_btn.grid(row=0, column=2, padx=5, pady=5)

        # --- 3. Export Section ---
        export_frame = ttk.LabelFrame(main_frame, text="3. Export Video")
        export_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        export_frame.columnconfigure(0, weight=1)
        
        self.export_btn = ttk.Button(export_frame, text="Combine and Export Video", command=self.start_export_thread)
        self.export_btn.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=10)

        # --- 4. Status Bar ---
        self.status_label = ttk.Label(main_frame, text="Ready.", relief=tk.SUNKEN, anchor="w", padding=5)
        self.status_label.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=(5,0))

    # --- Video Clip Functions ---
    def add_video_clips(self):
        """Opens a file dialog to select one or more video files."""
        filepaths = filedialog.askopenfilenames(
            title="Select Video Clips",
            filetypes=[
                ("Video Files", "*.mp4 *.avi *.mov *.mkv"), 
                ("All Files", "*.*")
            ]
        )
        if filepaths:
            for f in filepaths:
                self.video_clips.append(f)
                self.video_listbox.insert(tk.END, os.path.basename(f))
            self.update_status(f"{len(filepaths)} clip(s) added.")

    def remove_video_clip(self):
        """Removes the selected video clip from the list."""
        try:
            selected_index = self.video_listbox.curselection()[0]
            self.video_listbox.delete(selected_index)
            removed_clip = self.video_clips.pop(selected_index)
            self.update_status(f"Removed: {os.path.basename(removed_clip)}")
        except IndexError:
            self.update_status("No clip selected to remove.")
            
    def move_clip_up(self):
        """Moves the selected clip up in the list."""
        try:
            idx = self.video_listbox.curselection()[0]
            if idx == 0:
                return # Can't move up if already at top
            
            # Swap in the list
            path = self.video_clips.pop(idx)
            self.video_clips.insert(idx - 1, path)
            
            # Update listbox
            self.refresh_listbox()
            self.video_listbox.selection_set(idx - 1)
        except IndexError:
            pass # No selection

    def move_clip_down(self):
        """Moves the selected clip down in the list."""
        try:
            idx = self.video_listbox.curselection()[0]
            if idx == len(self.video_clips) - 1:
                return # Can't move down if at bottom
            
            # Swap in the list
            path = self.video_clips.pop(idx)
            self.video_clips.insert(idx + 1, path)
            
            # Update listbox
            self.refresh_listbox()
            self.video_listbox.selection_set(idx + 1)
        except IndexError:
            pass # No selection
            
    def refresh_listbox(self):
        """Clears and re-populates the listbox from self.video_clips."""
        self.video_listbox.delete(0, tk.END)
        for path in self.video_clips:
            self.video_listbox.insert(tk.END, os.path.basename(path))

    # --- Music Functions ---
    def add_music(self):
        """Opens a file dialog to select one music file."""
        filepath = filedialog.askopenfilename(
            title="Select Music File",
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg"), ("All Files", "*.*")]
        )
        if filepath:
            self.music_file = filepath
            self.music_label.config(text=os.path.basename(filepath))
            self.update_status(f"Added music: {os.path.basename(filepath)}")

    def remove_music(self):
        """Removes the music file."""
        self.music_file = None
        self.music_label.config(text="No music selected.")
        self.update_status("Music removed.")
        
    def update_status(self, text):
        """Updates the status bar text."""
        self.status_label.config(text=text)

    # --- Export Functions (with Threading) ---
    def start_export_thread(self):
        """
        Starts the video export process in a separate thread to avoid
        freezing the GUI.
        """
        if not self.video_clips:
            messagebox.showerror("No Videos", "Please add at least one video clip to export.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Save Video As...",
            filetypes=[("MP4 Video", "*.mp4")],
            defaultextension=".mp4"
        )
        if not save_path:
            self.update_status("Export cancelled.")
            return

        # Disable buttons to prevent changes during export
        self.set_ui_state(tk.DISABLED)
        self.update_status(f"Exporting to {os.path.basename(save_path)}...")

        # Run the heavy 'export_video' function in a new thread
        export_thread = threading.Thread(
            target=self.export_video, 
            args=(save_path,),
            daemon=True # Allows app to close even if thread is running
        )
        export_thread.start()

    def export_video(self, save_path):
        """
        This function runs in a separate thread.
        It uses moviepy to combine clips and add audio.
        """
        try:
            # 1. Load video clips
            self.update_status("Loading video clips...")
            clips = [VideoFileClip(path) for path in self.video_clips]

            # 2. Concatenate (stitch) them together
            final_clip = concatenate_videoclips(clips, method="compose")

            # 3. Add music if provided
            if self.music_file:
                self.update_status("Adding music...")
                audio = AudioFileClip(self.music_file)
                
                # If music is longer than video, cut it to video length
                if audio.duration > final_clip.duration:
                    audio = audio.subclip(0, final_clip.duration)
                
                # Set the video's audio to the new audio clip
                final_clip = final_clip.with_audio(audio)

            # 4. Write the final file
            # This is the slowest part.
            self.update_status("Writing video file (this may take a while)...")
            final_clip.write_videofile(
                save_path, 
                codec='libx264',      # Standard video codec
                audio_codec='aac',    # Standard audio codec
                logger='bar'          # Shows progress bar in console
            )

            # 5. Clean up moviepy objects
            for clip in clips:
                clip.close()
            if self.music_file:
                audio.close()

            # 6. Report success back to the main thread
            self.root.after(0, self.on_export_success, save_path)

        except Exception as e:
            # 7. Report errors back to the main thread
            self.root.after(0, self.on_export_error, str(e))
        finally:
            # 8. Re-enable the UI in the main thread
            self.root.after(0, self.set_ui_state, tk.NORMAL)

    def set_ui_state(self, state):
        """Disables or enables all interactive widgets."""
        self.add_video_btn.config(state=state)
        self.remove_video_btn.config(state=state)
        self.move_up_btn.config(state=state)
        self.move_down_btn.config(state=state)
        self.add_music_btn.config(state=state)
        self.remove_music_btn.config(state=state)
        self.export_btn.config(state=state)
        # Also set listbox state
        if state == tk.DISABLED:
            self.video_listbox.config(state=tk.DISABLED)
        else:
            self.video_listbox.config(state=tk.NORMAL)


    # --- Thread Callback Functions ---
    # These functions are called from the main thread (via root.after)
    # to safely update the GUI.

    def on_export_success(self, save_path):
        """Called when the export finishes successfully."""
        messagebox.showinfo("Export Complete", f"Video saved to:\n{save_path}")
        self.update_status("Ready.")

    def on_export_error(self, error_message):
        """Called if the export fails."""
        messagebox.showerror("Export Error", f"An error occurred:\n{error_message}")
        self.update_status("Export failed. Ready.")


# --- Main execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = VideoEditorApp(root)
    root.mainloop()
