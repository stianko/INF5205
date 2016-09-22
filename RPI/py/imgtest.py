import Image, ImageTk
import Tkinter 
from time import sleep

img = Image.open('picture.jpg')
img = img.resize((320, 240), Image.ANTIALIAS)
img2 = Image.open('img.jpg')




count = 0;
while(count < 2):
    root = Tkinter.Tk()
    if (count == 1):
        tkimage = ImageTk.PhotoImage(img)
        Tkinter.Label(root, image=tkimage).pack()
        root.update_idletasks()
        root.update()
        print 'Displaying first image'
        sleep(3)
    else:
        tkimage = ImageTk.PhotoImage(img2)
        Tkinter.Label(root, image=tkimage).pack()
        root.update_idletasks()
        root.update()
        print 'displaying second image'
        sleep(3)
    root.destroy()
    count = count+1
    
    

#root.mainloop()
root.quit()
# print img.format, img.size, img.mode
# img.show()
