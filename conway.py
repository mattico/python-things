# Matt Ickstadt

import json
from collections import defaultdict
from tkinter import *
from tkinter import filedialog
import sys

# The grid class represents the Universe at one instance in time.
class Grid():
    def __init__(self):
        self.cells = set()

    # returns a set of the (x,y) which are in the neighborhood of a cell
    def nh(self, cell):
        nh = ((-1, 1), (0, 1), (1, 1),
              (-1, 0),         (1, 0),
              (-1,-1), (0,-1), (1,-1))
        return list(((cell[0]+offset[0], cell[1]+offset[1]) for offset in nh))

    # Each cell is drawn as a 9x9 dark grey square
    def drawCell(self, cell, canvas):
        return canvas.create_rectangle(cell[0]*10+1, cell[1]*10+1, cell[0]*10+9, cell[1]*10+9, fill="#222")


    def addCell(self, cell, canvas=None):
        self.cells.add(cell)
        handle = None
        if canvas is not None:
            handle = self.drawCell(cell, canvas)
            self.setScrollBounds(canvas)
        return handle

    def removeCell(self, handle, canvas=None):
        if canvas is not None:
            self.setScrollBounds(canvas)
            coords = canvas.coords(handle[0])

            cell = (int(coords[0]//10), int(coords[1]//10))

            self.cells.remove(cell)
            canvas.delete(handle[0])

    def toggleCell(self, cell, canvas=None):
        if cell in self.cells:
            self.removeCell(cell, canvas)
        else:
            self.addCell(cell, canvas)

    def drawAll(self, canvas):
        canvas.delete(ALL)
        for cell in self.cells:
            self.drawCell(cell, canvas)
        self.setScrollBounds(canvas)

    # duplicate of MainWindow.__ssetScrollBounds b/c lazy
    # updates the scrollbounds to be large enough to contain
    # everything on the canvas.  Allows you to actually scroll
    # all the way to every cell
    def setScrollBounds(self, canvas):
        bbox = canvas.bbox(ALL)
        if bbox is not None:
            canvas.config(scrollregion=(0, 0, bbox[2], bbox[3]))

    def isAlive(self, cell):
        return (x, y) in self.cells

    # returns a grid representing the next generation
    def next(self):
        nhCells = defaultdict(int)

        # nhCells will be a dict relating (x,y) tuples
        # to ints, where the int value is the number of
        # cells that cell *is a neighbor of*.
        for cell in self.cells:
            for c in self.nh(cell):
                nhCells[c] += 1

        nextGrid = Grid()
        for cell in nhCells:

            # If a cell is the neighbor of 3 cells, it will be enabled.
            # If a cell is the neighbor of 2 cells and is currently
            # enabled, it will be enabled.
            if nhCells[cell] == 3:
                nextGrid.addCell(cell)
            elif nhCells[cell] == 2 and cell in self.cells:
                nextGrid.addCell(cell)

        return nextGrid

class MainWindow(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent)

        self.__parent = parent
        self.__filePath = ""
        self.__running = False
        self.__currentGeneration = 0
        self.__canvas = None

        self.__grids = []
        self.__grids.append(Grid())

    # Initialize the ui elements
    def initUI(self):
        self.__parent.title("Life - No File")
        self.pack(fill=BOTH, expand=1)

        self.__menuBar = Menu(self.__parent)
        self.__parent.config(menu=self.__menuBar)

        fileMenu = Menu(self.__menuBar)
        exampleMenu = Menu(fileMenu)

        add = exampleMenu.add_command
        add(label="Gosper", command=self.openGosper)
        add(label="1-High Infinite Replicator", command=self.open1Inf)
        add(label="Queen Bee Shuttle", command=self.openBeeShuttle)
        add(label="Pulsar", command=self.openPulsar)
        add(label="Puff Train", command=self.openPuffTrain)

        add = fileMenu.add_command
        add(label="New", command=self.onNew)
        add(label="Open", command=self.onOpen)
        fileMenu.add_cascade(label="Open Example", menu=exampleMenu)
        add(label="Save", command=self.onSave)
        add(label="Save As", command=self.onSaveAs)
        fileMenu.add_separator()
        add(label="Exit", command=self.onExit)

        self.__menuBar.add_cascade(label="File", menu=fileMenu)

        self.__menuBar.add_separator()

        add = self.__menuBar.add_command
        add(label="\u23ee", command=self.onFirst)
        add(label="\u25c2", command=self.onPrevious)
        add(label="\u25B6", command=self.onPlayPause) # index 4
        add(label="\u25b8", command=self.onNext)
        add(label="\u23ed", command=self.onLast)

        self.__menuBar.add_separator()

        # Generation label has to be a button since you can't put labels on a menuBar
        add(label="0/0") # index 10

        # using frame for layout, since .pack() would put one of the
        # scrollbar buttons in the corner of the window
        frame = Frame(self, bd=2, relief=SUNKEN)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        xscrollbar = Scrollbar(frame, orient=HORIZONTAL)
        xscrollbar.grid(row=1, column=0, sticky=E+W) # Bottom-left, sticky left-right

        yscrollbar = Scrollbar(frame, orient=VERTICAL)
        yscrollbar.grid(row=0, column=1, sticky=N+S) # top-right, sticky top-bot

        self.__canvas = Canvas(frame, bd=0, bg="#FFFFFF",
                               xscrollcommand=xscrollbar.set,
                               yscrollcommand=yscrollbar.set)
        self.__canvas.grid(row=0, column=0, sticky=N+S+E+W) # top-left

        # (row=1, column=1)/bot-right is the empty square

        # scroll the canvas
        xscrollbar.config(command=self.__canvas.xview)
        yscrollbar.config(command=self.__canvas.yview)

        frame.pack(fill=BOTH, expand=1)

        # bind onCanvasClick to all left mouse events on the canvas
        self.__canvas.bind('<ButtonPress-1>', self.onCanvasClick)

        # bind key presses
        self.__parent.bind('<space>', self.onPlayPause)
        self.__parent.bind('<Right>', self.onNext)
        self.__parent.bind('<Left>', self.onPrevious)
        self.__parent.bind('<Control-Left>', self.onFirst)
        self.__parent.bind('<Control-Right>', self.onLast)
        self.__parent.bind('<Control-n>', self.onNew)
        self.__parent.bind('<Control-o>', self.onOpen)
        self.__parent.bind('<Control-s>', self.onSave)
        self.__parent.bind('<Control-q>', self.onExit)

# Event Handlers
    def onNew(self, event=None):
        self.clear()
        self.__setCurrentFile("")

    def onOpen(self, event=None):
        self.__setCurrentFile(filedialog.askopenfilename(filetypes=(("Conway files", "*.con"),
                                                                    ("All files", "*.*"))))
        self.load()

    def onSave(self, event=None):
        if self.__filePath == '':
            return self.onSaveAs()
        self.save()

    def onSaveAs(self, event=None):
        self.__setCurrentFile(filedialog.asksaveasfilename(filetypes=(("Conway files", "*.con"),
                                                                      ("All files", "*.*"))))
        self.save()

    def onExit(self, event=None):
        self.quit()

    def onFirst(self, event=None):
        self.__running = False
        self.__setGeneration(0)
    def onPrevious(self, event=None):
        self.__running = False
        if self.__currentGeneration > 0:
            self.__setGeneration(self.__currentGeneration - 1)

    def onPlayPause(self, event=None):
        self.__running = not self.__running
        if self.__running:
            self.__menuBar.entryconfigure(4, label="\u25fc")
            self.loop()
        else:
            self.__menuBar.entryconfigure(4, label="\u25B6")

    def onNext(self, event=None):
        self.__running = False
        self.__setGeneration(self.__currentGeneration + 1)

    def onLast(self, event=None):
        self.__running = False
        self.__setGeneration(len(self.__grids)-1)

    def onCanvasClick(self, event=None):
        if self.__canvas.find_withtag(CURRENT) is () or None:
            self.__grids[self.__currentGeneration].addCell((int(event.x//10), int(event.y//10)), self.__canvas)
        else:
            self.__grids[self.__currentGeneration].removeCell(self.__canvas.find_withtag(CURRENT), self.__canvas)
        self.updateFuture()

    def openGosper(self):
        data = set([(9, 8), (30, 8), (43, 6), (28, 5), (24, 9), (18, 9), (23, 10), (19, 6),
            (43, 5), (8, 7), (32, 4), (28, 7), (29, 6), (20, 11), (18, 7), (42, 5), (24, 8),
            (32, 9), (30, 4), (25, 8), (18, 8), (42, 6), (21, 5), (32, 3), (23, 6), (19, 10),
            (28, 6), (9, 7), (29, 7), (21, 11), (20, 5), (24, 7), (8, 8), (22, 8), (32, 8), (29, 5)])

        self.clear()
        self.__setCurrentFile("")
        for cell in data:
            self.__grids[0].addCell(cell, self.__canvas)

    def open1Inf(self):
        data = set([(52, 39), (26, 39), (21, 39), (42, 39), (51, 39), (46, 39), (25, 39),
            (50, 39), (20, 39), (45, 39), (15, 39), (33, 39), (23, 39), (41, 39), (31, 39),
            (24, 39), (49, 39), (19, 39), (44, 39), (14, 39), (32, 39), (18, 39), (27, 39),
            (40, 39), (48, 39), (43, 39), (17, 39), (16, 39)])

        self.clear()
        self.__setCurrentFile("")
        for cell in data:
            self.__grids[0].addCell(cell, self.__canvas)

    def openBeeShuttle(self):
        data = set([(21, 9), (22, 9), (24, 13), (23, 10), (22, 15), (23, 14), (24, 11), (21, 15), (24, 12)])

        self.clear()
        self.__setCurrentFile("")
        for cell in data:
            self.__grids[0].addCell(cell, self.__canvas)

    def openPulsar(self):
        data = set([(21, 14), (21, 15), (22, 13), (22, 12), (22, 15), (22, 16), (23, 14), (23, 15), (23, 13), (21, 13)])

        self.clear()
        self.__setCurrentFile("")
        for cell in data:
            self.__grids[0].addCell(cell, self.__canvas)

    def openPuffTrain(self):
        data = set([(26, 14), (22, 13), (23, 22), (26, 28), (22, 27), (24, 14), (26, 12),
            (24, 19), (25, 11), (26, 26), (24, 28), (25, 25), (23, 14), (25, 14), (26, 13),
            (25, 28), (24, 20), (23, 19), (26, 27), (23, 28), (22, 18), (24, 21)])

        self.clear()
        self.__setCurrentFile("")
        for cell in data:
            self.__grids[0].addCell(cell, self.__canvas)

    # loads the current self.__filePath
    def load(self):
        self.clear()
        print("loading: ", self.__filePath)
        self.__grids.append(Grid())
        if self.__filePath != "" and self.__filePath is not None:
            file = open(self.__filePath, 'r')
            data = json.load(file)
            file.close()
            for cell in data["data"]:
                self.__grids[0].addCell(tuple(cell), self.__canvas)

    # saves to the current self.__filePath
    def save(self):
        print("saving: ", self.__filePath)
        if self.__filePath != "" and self.__filePath is not None:
            file = open(self.__filePath, 'w')
            json.dump({
                    "data": [list(c) for c in self.__grids[0].cells],
                    "generation": len(self.__grids)
                }, file)
            file.close()

    def __setCurrentFile(self, fileName):
        self.__filePath = fileName
        if fileName == "":
            self.__parent.title("Life - No File")
        else:
            self.__parent.title("Life - " + fileName)

    def __setGeneration(self, generation):
        while generation >= len(self.__grids):
            self.__grids.append(self.__grids[-1].next())
        self.__currentGeneration = generation
        self.__grids[self.__currentGeneration].drawAll(self.__canvas)

        # set the generation label
        self.__menuBar.entryconfigure(10, label="{}/{}".format(generation, len(self.__grids)-1))

    def loop(self):
        if self.__running:
            self.__setGeneration(self.__currentGeneration + 1)
            self.after(100, self.loop)

    def updateFuture(self):
        for idx in range(self.__currentGeneration, len(self.__grids)-1):
            self.__grids[idx+1] = self.__grids[idx].next()

    # expands the scroll region to include all objects on the canvas
    def setScrollBounds(self):
        bbox = self.__canvas.bbox(ALL)
        if bbox is not None:
            self.__canvas.config(scrollregion=(0, 0, bbox[2], bbox[3]))

    # clears all state except the file name
    def clear(self):
        self.__running = False
        self.__currentGeneration = 0
        self.__canvas.delete(ALL)
        self.__grids = [Grid()]
        self.__menuBar.entryconfigure(10, label="0/0") # reset the generation label
        self.__menuBar.entryconfigure(4, label="\u25B6") # reset the play-pause button

# entry point of the application
def main():
    root = Tk()
    root.geometry("500x300")
    root.option_add("*tearOff", FALSE) # prevent those annoying dashed line things

    app = MainWindow(root)
    app.initUI()

    root.mainloop()

# in interactive mode, let the user decide to run main or not
if __name__ == "__main__" and not sys.flags.interactive:
    main()