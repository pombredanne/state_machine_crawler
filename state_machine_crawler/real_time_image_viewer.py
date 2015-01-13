import os

from Tkinter import PhotoImage, Tk, Canvas, VERTICAL, HORIZONTAL, BOTTOM, RIGHT, LEFT, Y, X, BOTH, Scrollbar


class StatusObject:

    def __init__(self):
        self.alive = True


def run_viewer(file_name, status_object=None):

    status_object = status_object or StatusObject()

    viewer = Tk()
    viewer.title(file_name)

    while not os.path.exists(file_name):
        if status_object.alive:
            continue
        else:
            return

    ok = False

    while not ok:
        if not status_object.alive:
            return
        try:
            img = PhotoImage(file=file_name)
            ok = True
        except:
            pass

    canvas = Canvas(viewer, width=min(img.width(), 1024), heigh=min(img.height(), 768),
                    scrollregion=(0, 0, img.width(), img.height()))

    hbar = Scrollbar(viewer, orient=HORIZONTAL)
    hbar.config(command=canvas.xview)

    vbar = Scrollbar(viewer, orient=VERTICAL)
    vbar.config(command=canvas.yview)

    image_on_canvas = canvas.create_image(img.width() / 2, img.height() / 2, image=img)
    canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

    hbar.pack(side=BOTTOM, fill=X)
    vbar.pack(side=RIGHT, fill=Y)
    canvas.pack(side=LEFT, expand=True, fill=BOTH)

    def _refresh_viewer():
        try:
            refreshed_photo = PhotoImage(file=file_name)
            canvas.itemconfig(image_on_canvas, image=refreshed_photo)
            canvas.img = refreshed_photo
        except:
            pass

    def loop():
        _refresh_viewer()
        if not status_object.alive:
            viewer.quit()
            return
        viewer.after(50, loop)

    loop()
    viewer.mainloop()


def main():
    run_viewer("/tmp/testrun.png")

if __name__ == "__main__":
    main()
