import Image, ImageTk
import Tkinter 


img = Image.open('picture.jpg')

root = Tkinter.Tk()

tkimage = ImageTk.PhotoImage(img)

Tkinter.Label(root, image=tkimage).pack()

root.mainloop()

# print img.format, img.size, img.mode
# img.show()
