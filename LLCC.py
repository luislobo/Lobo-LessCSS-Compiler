# Lobo LessCSS Compiler
# Version: 1.0
# License: MIT
# Author: Luis Lobo Borobia
# Email: lobo@fictioncity.net, luislobo@gmail.com
# Uses https://github.com/seb-m/pyinotify to get notifications from file disk
# Uses libnode-less Ubuntu package for compiling LESS files
"""
Lobo LessCSS Compiler

@author: Luis Lobo Borobia
@license: MIT License
@contact: luislobo@gmail.com
"""
import os
import wx
import pyinotify
import json

def alert(message):
	wx.MessageBox(message, 'Alert', wx.OK | wx.ICON_INFORMATION)

class MainWindow(wx.Frame):
	def __init__(self, parent, title):

		# Initializes pyinotify objects
		self.wm = None
		self.notifier = None
		self.stopWatching = 0
		self.directories = dict()
		
		# Create main frame
		wx.Frame.__init__(self, parent, title=title, size=(500, 500))

		# Init the GUI
		self.InitGUI()

		#show GUI
		self.Show(True)

	def OnExit(self, e):
		self.Close(True)  # Close the frame.

	def InitGUI(self):
		
		# Main Panel
		self.mainPanel = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
		
		# add button to pannel
		hbButtons = wx.BoxSizer(wx.HORIZONTAL)
		self.addDirectoryButton = wx.Button(self.mainPanel, 1, "Add Directory to watch")
		self.removeDirectoryButton = wx.Button(self.mainPanel, 2, "Remove Directory from list")
		self.startWatchingButton = wx.ToggleButton(self.mainPanel, 3, "Start watching")
		hbButtons.Add(self.addDirectoryButton, 2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)
		hbButtons.Add(self.removeDirectoryButton, 2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)
		hbButtons.Add(self.startWatchingButton, 2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)

		# Add config list to panel
		self.configList = ConfigListBox(self.mainPanel)
		self.ReadDirectories()

		# Add controls to vertical box sizer
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(hbButtons, 0, flag=wx.EXPAND | wx.LEFT | wx.TOP | wx.RIGHT, border=5)
		vbox.Add(wx.StaticText(self.mainPanel, -1, "Folders being watched", style=wx.ALIGN_CENTRE),
			0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=5)
		vbox.Add(self.configList, 2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5)

		self.mainPanel.SetSizer(vbox)

		# A StatusBar in the bottom of the window
		self.statusBar = self.CreateStatusBar() 

		# Setting up the menu.
		filemenu = wx.Menu()

		# wx.ID_ABOUT and wx.ID_EXIT are standard ids provided by wxWidgets.
		self.menuExit = filemenu.Append(wx.ID_EXIT, "E&xit", " Terminate the program")

		# Creating the menubar.
		menuBar = wx.MenuBar()
		menuBar.Append(filemenu, "&File") # Adding the "filemenu" to the MenuBar
		self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.

		self.Centre()

		# Set events.
		self.Bind(wx.EVT_MENU, self.OnExit, self.menuExit)
		self.Bind(wx.EVT_BUTTON, self.OnAddDirectory, self.addDirectoryButton)
		self.Bind(wx.EVT_BUTTON, self.OnRemoveDirectory, self.removeDirectoryButton)
		
		self.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartWatching, self.startWatchingButton)
		self.Bind(wx.EVT_CLOSE, self.OnClose)

	def ReadDirectories(self):
		self.directories = dict()
		for directory in self.configList.Items:
			self.directories[directory] = None
	
	def OnClose(self, event):
		# stop notifier
		self.StopWatching()
		self.configList.saveList()
		self.Destroy()

	def StartWatching(self):
		self.stopWatching = 0
		if self.wm is None:
			self.wm = pyinotify.WatchManager()
			if self.notifier is None:
				self.notifier = pyinotify.Notifier(self.wm, EventHandler(),timeout=10)
				self.ReadDirectories()
				for k in self.directories.keys():
					self.AddPathToWatch(k)
					self.setSBMessage("Adding: " + k)
				self.setSBMessage("Watching...")
				
				# process Events
				while True:
					if self.stopWatching:
						if not self.wm is None:
							self.notifier = None
							self.wm.close()
							self.wm = None
							self.directories = dict()
						self.setSBMessage("Not Watching...")					
						break
					self.notifier.process_events()
					if self.notifier.check_events():
						self.notifier.read_events()
					wx.Yield()
		
	def StopWatching(self):
		# TODO: handle a better way to see if thread is running
		self.stopWatching = 1

	def AddPathToWatch(self, path):
		# watched events
		if not path in self.directories:
			self.configList.Append(path)
			self.configList.saveList()
		mask = pyinotify.IN_CLOSE_WRITE
		self.directories[path] = self.wm.add_watch(path, mask, rec=False)

	def OnAddDirectory(self, event):
		self.OpenDirectory()
		
	def OnRemoveDirectory(self,event):
		self.RemoveSelectedDirectory()
	
	def RemoveSelectedDirectory(self):
		sel = self.configList.GetSelection()
		if not sel == wx.NOT_FOUND:
			directory = self.configList.Items[sel]
			if self.directories[directory] != None:
				self.wm.rm_watch(self.directories[directory],rec=False)
			del self.directories[directory]
			self.configList.Delete(sel)

	def OnStartWatching(self, event):
		# TODO: handle a better way to see if thread is running
		# If it's pressed, means it is already running
		startIsPressed = self.startWatchingButton.GetValue()

		if startIsPressed:
			self.startWatchingButton.SetLabel("Stop Watching")
			self.StartWatching()
		else:
			self.startWatchingButton.SetLabel("Start Watching")
			self.StopWatching()
		
	def OpenDirectory(self):
		dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE)
		if dlg.ShowModal() == wx.ID_OK:
			self.AddPathToWatch(dlg.GetPath())
		dlg.Destroy()
		
	def setSBMessage(self, message):
		frame.statusBar.SetStatusText(message)

class EventHandler(pyinotify.ProcessEvent):
	def process_IN_CLOSE_WRITE(self, event):
		fileName, fileExtension = os.path.splitext(event.pathname)
		if fileExtension == ".less":
			frame.setSBMessage("Compiling: " + fileName + '.css')
			command = 'lessc -x %s > %s' % (event.pathname, fileName + '.css')
			#alert(command)
			os.system(command)
			frame.setSBMessage("Compiled: " + fileName + '.css')

class ConfigListBox(wx.ListBox):

	def __init__(self, *args, **kwargs):
		wx.ListBox.__init__(self, *args, **kwargs)
		self.config = wx.Config("LLCCConfig")
		self.fillList()

	def fillList(self):
		dirsToWatch = None
		try:
			# load rows and check for error too, if no data
			if self.config.Exists(u"DirectoriesToWatch"):
				dirsToWatch = str(self.config.Read(u"DirectoriesToWatch", ""))
				if not dirsToWatch == "":
					self.Items = json.loads(dirsToWatch)
		except:
			pass

	def saveList(self):
		itemsJson = json.dumps(self.Items)
		self.config.Write("DirectoriesToWatch", itemsJson)
		self.config.Flush()

if __name__ == '__main__':
	app = wx.App(False)
	frame = MainWindow(None, "Lobo LessCSS compiler")
	app.MainLoop()
