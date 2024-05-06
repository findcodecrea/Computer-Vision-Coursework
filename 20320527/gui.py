import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

import numpy as np
from PIL import Image, ImageTk, ImageEnhance, ImageFilter

from stitcher import process_video
from utils import setup_logging

setup_logging()

filename = None
global canva, image_canva, load1, render, brightness_slider, contrast_slider, blur_slider, saturation_slider, \
    sharpen_slider, img, original_img, photo, canvas, image_on_canvas, load2, load3, entry1, entry2, entry3


def select_video():
    global filename
    filename = filedialog.askopenfilename(title="Select Video File",
                                          filetypes=(("MP4 files", "*.mp4"), ("All files", "*.*")))
    if filename:
        file_label.config(text=f"File: {filename}")


def start_processing():
    global filename
    if not filename:
        messagebox.showerror("Error", "Please select a video file first.")
        return
    threading.Thread(target=lambda: process_video(filename, update_gui, update_progress), daemon=True).start()


def move_canvas(canvass, direction):
    if direction == 'up':
        canvass.yview_scroll(-1, 'units')
    elif direction == 'down':
        canvass.yview_scroll(1, 'units')
    elif direction == 'left':
        canvass.xview_scroll(-1, 'units')
    elif direction == 'right':
        canvass.xview_scroll(1, 'units')


def on_entry_click(event, default_text):
    """Entry click event handler."""
    if event.widget.get() == default_text:
        event.widget.delete(0, tk.END)
        event.widget.config(fg='black')


def on_focusout(event, default_text):
    """Entry focus out event handler."""
    if not event.widget.get():
        event.widget.insert(0, default_text)
        event.widget.config(fg='grey')


def update_gui(progress_message, image=None):
    progress_label.config(text=progress_message)
    if image is not None:
        new_window = tk.Toplevel(root)
        new_window.title("Stitched Image")
        new_window.geometry("1200x600")
        global load1
        with Image.open(image) as load1:
            width, height = load1.size
            new_height = 500
            new_width = width * (new_height/height)
            load = load1.resize((int(new_width), new_height))
        global render
        render = ImageTk.PhotoImage(load)
        global canva
        canva = tk.Canvas(new_window, width=1200, height=500)
        global image_canva
        image_canva = canva.create_image(0, 0, image=render, anchor="nw")
        canva.image = render  # keep a reference
        canva.pack()

        button_frame = tk.Frame(new_window)
        button_frame.pack(fill=tk.X)

        left_button = tk.Button(button_frame, text="Left", command=lambda: move_canvas(canva, 'left'))
        left_button.pack(side=tk.LEFT, padx=10)

        right_button = tk.Button(button_frame, text="Right", command=lambda: move_canvas(canva, 'right'))
        right_button.pack(side=tk.LEFT, padx=10)

        up_button = tk.Button(button_frame, text="Up", command=lambda: move_canvas(canva, 'up'))
        up_button.pack(side=tk.LEFT, padx=10)

        down_button = tk.Button(button_frame, text="Down", command=lambda: move_canvas(canva, 'down'))
        down_button.pack(side=tk.LEFT, padx=10)

        save_button = tk.Button(button_frame, text="Save Image", command=lambda: save_image(load1))
        save_button.pack(side=tk.LEFT, padx=20)

        edit_button = tk.Button(button_frame, text="Open Image Editor", command=lambda: open_editor())
        edit_button.pack(side=tk.RIGHT, padx=20)

        # create two input boxes
        global entry1, entry2, entry3
        # Entry for black_threshold
        entry1 = tk.Entry(button_frame, fg='grey')
        entry1.insert(0, 'black_threshold')
        entry1.bind('<FocusIn>', lambda event, text='black_threshold': on_entry_click(event, text))
        entry1.bind('<FocusOut>', lambda event, text='black_threshold': on_focusout(event, text))
        entry1.pack(side=tk.RIGHT)

        # Entry for black_ratio_threshold
        entry2 = tk.Entry(button_frame, fg='grey', width=30)
        entry2.insert(0, 'black_ratio_threshold(float)')
        entry2.bind('<FocusIn>', lambda event, text='black_ratio_threshold(float)': on_entry_click(event, text))
        entry2.bind('<FocusOut>', lambda event, text='black_ratio_threshold(float)': on_focusout(event, text))
        entry2.pack(side=tk.RIGHT)

        # Entry for black_threshold
        entry3 = tk.Entry(button_frame, fg='grey')
        entry3.insert(0, 'x or y or both')
        entry3.bind('<FocusIn>', lambda event, text='x or y or both': on_entry_click(event, text))
        entry3.bind('<FocusOut>', lambda event, text='x or y or both': on_focusout(event, text))
        entry3.pack(side=tk.RIGHT)

        trim_button = tk.Button(button_frame, text="Trim black edges", command=lambda: black_crop())
        trim_button.pack(side=tk.RIGHT, padx=20)

        clarity_label = tk.Label(new_window, text="The saved image will be clearer than displayed in the interface.")
        clarity_label.pack(side=tk.BOTTOM)

        clarity1_label = tk.Label(new_window, text="Please enter the threshold and direction that needs to be clipped before click the trim button.")
        clarity1_label.pack(side=tk.BOTTOM)


def black_crop():
    # Get input values and provide default values
    black_threshold = float(entry1.get() if (entry1.get() != 'black_threshold' and entry1.get() != '') else 5)
    black_ratio_threshold = float(entry2.get() if (entry2.get() != 'black_ratio_threshold(float)' and entry2.get() != '') else 1 / 3)
    coordinate = entry3.get() if (entry3.get() != 'x or y or both' and entry3.get() != '') else 'both'

    # Loading images
    image_path = 'images/result.png'  # Replace it with your image file path
    image = Image.open(image_path)

    # Convert the image to an array
    image_array = np.array(image)

    # The proportion of black pixels is calculated for each row and column
    if coordinate in ('both', 'y'):
        black_columns_ratio = (image_array <= black_threshold).sum(axis=0) / image_array.shape[0]
        valid_columns = np.where(black_columns_ratio < black_ratio_threshold)[0]
        left, right = valid_columns[0], valid_columns[-1]
    else:
        left, right = 0, image_array.shape[1] - 1  # Select all columns when no columns are screened

    if coordinate in ('both', 'x'):
        black_rows_ratio = (image_array <= black_threshold).sum(axis=1) / image_array.shape[1]
        valid_rows = np.where(black_rows_ratio < black_ratio_threshold)[0]
        top, bottom = valid_rows[0], valid_rows[-1]
    else:
        top, bottom = 0, image_array.shape[0] - 1  # Select all rows when no rows are screened

    # crop picture
    cropped_image = image.crop((left, top, right + 1, bottom + 1))
    cropped_image.save('images/result.png')  # Save the cropped image to a new file

    # Update the display of images in the Tkinter interface
    global render, load1
    with Image.open("images/result.png") as load1:
        width, height = load1.size
        new_height = 500
        new_width = int(width * (new_height / height))
        load = load1.resize((new_width, new_height))
        render = ImageTk.PhotoImage(load)
        canva.itemconfig(image_canva, image=render)


def update_progress(progress, message):
    progress_label.config(text=message)
    progress_bar['value'] = progress
    root.update_idletasks()


def save_image(image_object):
    file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                             filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
    if file_path:
        image_object.save(file_path)


def open_editor():
    global brightness_slider, contrast_slider, blur_slider, saturation_slider, sharpen_slider
    editor = tk.Toplevel(root)
    editor.title("Image Editor")
    editor.geometry("800x800")
    # Load the image for editing
    global img, original_img, photo, canvas, image_on_canvas, load2, load3
    original_img = Image.open("images/result.png")
    with Image.open("images/result.png") as load3:
        width, height = load3.size
        new_height = 500
        new_width = width * (new_height / height)
        original_img = load3.resize((int(new_width), new_height))
    img = original_img.copy()
    load2 = load3.copy()
    photo = ImageTk.PhotoImage(img)
    canvas = tk.Canvas(editor, width=img.width, height=img.height)
    canvas.pack()
    image_on_canvas = canvas.create_image(0, 0, image=photo, anchor="nw")

    # Add sliders for different image adjustments
    ttk.Label(editor, text="Adjust Brightness").pack()
    brightness_slider = ttk.Scale(editor, from_=0.5, to=1.5, orient='horizontal', command=lambda s: apply_brightness(float(s)))
    brightness_slider.set(1.0)
    brightness_slider.pack(fill='x')

    ttk.Label(editor, text="Adjust Contrast").pack()
    contrast_slider = ttk.Scale(editor, from_=0.5, to=1.5, orient='horizontal', command=lambda s: apply_contrast(float(s)))
    contrast_slider.set(1.0)
    contrast_slider.pack(fill='x')

    ttk.Label(editor, text="Apply Gaussian Blur").pack()
    blur_slider = ttk.Scale(editor, from_=0, to=10, orient='horizontal', command=lambda s: apply_blur(int(float(s))))
    blur_slider.pack(fill='x')

    ttk.Label(editor, text="Adjust Saturation").pack()
    saturation_slider = ttk.Scale(editor, from_=0.5, to=1.5, orient='horizontal', command=lambda s: apply_saturation(float(s)))
    saturation_slider.set(1.0)
    saturation_slider.pack(fill='x')

    # Slider for sharpen adjustment
    ttk.Label(editor, text="Adjust Sharpness").pack()
    sharpen_slider = ttk.Scale(editor, from_=0.5, to=1.5, orient='horizontal', command=lambda s: apply_sharpen(float(s)))
    sharpen_slider.set(1.0)  # Default value
    sharpen_slider.pack(fill='x')

    clarity_label = tk.Label(editor, text="Image manipulation is irreversible. If you want to try the opposite, reset the image values.")
    clarity_label.pack(side=tk.BOTTOM)

    left_button = tk.Button(editor, text="Left", command=lambda: move_canvas(canvas, 'left'))
    left_button.pack(side=tk.LEFT, padx=10)

    right_button = tk.Button(editor, text="Right", command=lambda: move_canvas(canvas, 'right'))
    right_button.pack(side=tk.LEFT, padx=10)

    up_button = tk.Button(editor, text="Up", command=lambda: move_canvas(canvas, 'up'))
    up_button.pack(side=tk.LEFT, padx=10)

    down_button = tk.Button(editor, text="Down", command=lambda: move_canvas(canvas, 'down'))
    down_button.pack(side=tk.LEFT, padx=10)

    restore_button = ttk.Button(editor, text="Reset Image", command=lambda: restore_original_image())
    restore_button.pack(side=tk.RIGHT, padx=20)

    save_button = tk.Button(editor, text="Save Image", command=lambda: save_image(load2))
    save_button.pack(side=tk.RIGHT, padx=20)


def update_image():
    global photo
    photo = ImageTk.PhotoImage(img)
    canvas.itemconfig(image_on_canvas, image=photo)


def apply_brightness(level):
    global img, load2
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(level)
    enhancer = ImageEnhance.Brightness(load2)
    load2 = enhancer.enhance(level)
    update_image()


def apply_contrast(level):
    global img, load2
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(level)
    enhancer = ImageEnhance.Contrast(load2)
    load2 = enhancer.enhance(level)
    update_image()


def apply_blur(radius):
    global img, load2
    img = img.filter(ImageFilter.GaussianBlur(radius=radius))
    load2 = load2.filter(ImageFilter.GaussianBlur(radius=radius))
    update_image()


def apply_saturation(level):
    global img, load2
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(level)
    enhancer = ImageEnhance.Color(load2)
    load2 = enhancer.enhance(level)
    update_image()


def apply_sharpen(level):
    global img, load2
    sharpness = ImageEnhance.Sharpness(img)
    img = sharpness.enhance(level)
    sharpness = ImageEnhance.Sharpness(load2)
    load2 = sharpness.enhance(level)
    update_image()


def restore_original_image():
    """Restores the image to its original state."""
    global brightness_slider, contrast_slider, blur_slider, saturation_slider, sharpen_slider
    global img, original_img, load2, load3
    img = original_img.copy()
    load2 = load3
    # Reset all slider values
    brightness_slider.set(1.0)
    contrast_slider.set(1.0)
    blur_slider.set(0)
    saturation_slider.set(1.0)
    sharpen_slider.set(1.0)
    update_image()

# Setup the main window
root = tk.Tk()
root.title("Video Frame Stitcher")
root.geometry("800x400")
root.style = ttk.Style()
root.style.theme_use('clam')

file_label = ttk.Label(root, text="Please select a video file.")
file_label.pack(pady=10)

select_button = ttk.Button(root, text="Select Video", command=select_video)
select_button.pack(pady=5)

start_button = ttk.Button(root, text="Start Processing", command=start_processing)
start_button.pack(pady=5)

progress_label = ttk.Label(root, text="Progress: ")
progress_label.pack(pady=10)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=200, mode="determinate")
progress_bar.pack(pady=20)

root.mainloop()
