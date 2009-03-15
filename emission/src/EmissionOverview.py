# -*- coding: utf-8 -*-

# GUI (Screens)
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox

# GUI (Components)
from Components.ActionMap import HelpableActionMap
from Components.Button import Button
from Components.FileList import FileList
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.List import List

# Configuration
from Components.config import config

from enigma import eTimer

try:
	from transmissionrpc import transmission
except ImportError:
	from transmission import transmission

import EmissionBandwidth
import EmissionDetailview
import EmissionSetup

LIST_TYPE_ALL = 0
LIST_TYPE_DOWNLOADING = 1
LIST_TYPE_SEEDING = 2

SORT_TYPE_TIME = 0
SORT_TYPE_PROGRESS = 1
SORT_TYPE_ADDED = 2
SORT_TYPE_SPEED = 3

class TorrentLocationBox(LocationBox):
	def __init__(self, session):
		# XXX: implement bookmarks
		LocationBox.__init__(self, session)

		self.skinName = "LocationBox"

		# non-standard filelist which shows .tor(rent) files
		self["filelist"] = FileList(None, showDirectories = True, showFiles = True, matchingPattern = "^.*\.tor(rent)?")

	def ok(self):
		# changeDir in booklist and only select path
		if self.currList == "filelist":
			if self["filelist"].canDescent():
				self["filelist"].descent()
				self.updateTarget()
			else:
				self.select()
		else:
			self["filelist"].changeDir(self["booklist"].getCurrent())

	def selectConfirmed(self, ret):
		if ret:
			dir = self["filelist"].getCurrentDirectory()
			cur = self["filelist"].getSelection()
			ret = dir and cur and dir + cur[0]
			if self.realBookmarks:
				if self.autoAdd and not ret in self.bookmarks:
					self.bookmarks.append(self.getPreferredFolder())
					self.bookmarks.sort()

				if self.bookmarks != self.realBookmarks.value:
					self.realBookmarks.value = self.bookmarks
					self.realBookmarks.save()
			self.close(ret)

	def select(self):
		# only go to work if a file is selected
		if self.currList == "filelist":
			if not self["filelist"].canDescent():
				self.selectConfirmed(True)

class EmissionOverview(Screen, HelpableScreen):
	skin = """<screen name="EmissionOverview" title="Torrent Overview" position="75,135" size="565,330">
		<widget size="320,25" alphatest="on" position="5,5" zPosition="1" name="all_sel" pixmap="skin_default/epg_now.png" />
		<widget valign="center" transparent="1" size="108,22" backgroundColor="#25062748" position="5,7" zPosition="2" name="all_text" halign="center" font="Regular;18" />
		<widget size="320,25" alphatest="on" position="5,5" zPosition="1" name="downloading_sel" pixmap="skin_default/epg_next.png" />
		<widget valign="center" transparent="1" size="108,22" backgroundColor="#25062748" position="111,7" zPosition="2" name="downloading_text" halign="center" font="Regular;18" />
		<widget size="320,25" alphatest="on" position="5,5" zPosition="1" name="seeding_sel" pixmap="skin_default/epg_more.png" />
		<widget valign="center" transparent="1" size="108,22" backgroundColor="#25062748" position="212,7" zPosition="2" name="seeding_text" halign="center" font="Regular;18" />
		<widget name="torrents" size="240,22" position="320,7" halign="right" font="Regular;18" />
		<!--ePixmap size="550,230" alphatest="on" position="5,25" pixmap="skin_default/border_epg.png" /-->
		<widget source="list" render="Listbox" position="5,30" size="550,225" scrollbarMode="showAlways">
			<convert type="TemplatedMultiContent">
				{"template": [
						MultiContentEntryText(pos=(2,2), size=(555,22), text = 1, font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(2,26), size=(555,18), text = 2, font = 1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
						(eListboxPythonMultiContent.TYPE_PROGRESS, 0, 44, 537, 6, -3),
					],
				  "fonts": [gFont("Regular", 20),gFont("Regular", 16)],
				  "itemHeight": 51
				 }
			</convert>
		</widget>
		<widget name="upspeed" size="150,20" position="5,260" halign="left" font="Regular;18" />
		<widget name="downspeed" size="150,20" position="410,260" halign="right" font="Regular;18" />
		<ePixmap position="0,290" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,290" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,290" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,290" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,290" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,290" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="280,290" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="420,290" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		self.transmission = transmission.Client(
			address = config.plugins.emission.hostname.value,
			port = config.plugins.emission.port.value,
			user = config.plugins.emission.username.value,
			password = config.plugins.emission.password.value
		)

		self["SetupActions"] = HelpableActionMap(self, "SetupActions",
		{
			"ok": (self.ok, _("show details")),
			"cancel": (self.close, _("close")),
		})

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"green": (self.bandwidth, _("open bandwidth settings")),
			"yellow": (self.prevlist, _("show previous list")),
			"blue": (self.nextlist, _("show next list")),
		})

		self["MenuActions"] = HelpableActionMap(self, "MenuActions",
		{
			"menu": (self.menu, _("open context menu")),
		})

		self["key_red"] = Button(_("Close"))
		self["key_green"] = Button(_("Bandwidth"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		self["all_text"] = Label(_("All"))
		self["downloading_text"] = Label(_("DL"))
		self["seeding_text"] = Label(_("UL"))
		self["upspeed"] = Label("")
		self["downspeed"] = Label("")
		self["torrents"] = Label("")

		self["all_sel"] = Pixmap()
		self["downloading_sel"] = Pixmap()
		self["seeding_sel"] = Pixmap()

		self['list'] = List([])

		self.list_type = config.plugins.emission.last_tab.value
		self.sort_type = config.plugins.emission.last_sort.value
		self.showHideSetTextMagic()

		self.timer = eTimer()
		self.timer.callback.append(self.updateList)
		self.timer.start(0, 1)

	def bandwidthCallback(self, ret = None):
		if ret:
			try:
				self.transmission.set_session(**ret)
			except transmission.TransmissionError:
				self.session.open(
					MessageBox,
					_("Could not connect to transmission-daemon!"),
					type = MessageBox.TYPE_ERROR,
					timeout = 5
				)
		self.updateList()

	def menuCallback(self, ret = None):
		ret and ret[1]()

	def newDlCallback(self, ret = None):
		if ret:
			try:
				res = self.transmission.add_url(ret)
			except transmission.TransmissionError:
				self.session.open(
					MessageBox,
					_("Could not connect to transmission-daemon!"),
					type = MessageBox.TYPE_ERROR,
					timeout = 5
				)
			else:
				if not res:
					self.session.open(
						MessageBox,
						_("Torrent could not be scheduled not download!"),
						type = MessageBox.TYPE_ERROR,
						timeout = 5
					)
		self.updateList()

	def newDl(self):
		self.timer.stop()
		self.session.openWithCallback(
			self.newDlCallback,
			TorrentLocationBox
		)

	def sortCallback(self, ret = None):
		if ret is not None:
			self.sort_type = config.plugins.emission.last_sort.value = ret[1]
			config.plugins.emission.last_sort.save()
		self.updateList()

	def sort(self):
		self.timer.stop()
		self.session.openWithCallback(
			self.sortCallback,
			ChoiceBox,
			_("Which sorting method do you prefer?"),
			[(_("by eta") ,SORT_TYPE_TIME),
			(_("by progress") ,SORT_TYPE_PROGRESS),
			(_("by age") ,SORT_TYPE_ADDED),
			(_("by speed") ,SORT_TYPE_SPEED)]
		)

	def pauseShown(self):
		self.transmission.stop([x[0].id for x in self.list])

	def unpauseShown(self):
		self.transmission.start([x[0].id for x in self.list])

	def pauseAll(self):
		try:
			self.transmission.stop([x.id for x in self.transmission.list().values()])
		except transmission.TransmissionError:
			self.session.open(
				MessageBox,
				_("Could not connect to transmission-daemon!"),
				type = MessageBox.TYPE_ERROR,
				timeout = 5
			)

	def unpauseAll(self):
		try:
			self.transmission.start([x.id for x in self.transmission.list().values()])
		except transmission.TransmissionError:
			self.session.open(
				MessageBox,
				_("Could not connect to transmission-daemon!"),
				type = MessageBox.TYPE_ERROR,
				timeout = 5
			)

	def configure(self):
		reload(EmissionSetup)
		self.timer.stop()
		self.session.openWithCallback(
			self.configureCallback,
			EmissionSetup.EmissionSetup
		)

	def menu(self):
		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			_("What do you want to do?"),
			[(_("Configure connection"), self.configure),
			(_("Change sorting"), self.sort),
			(_("Add new download"), self.newDl),
			(_("Pause shown"), self.pauseShown),
			(_("Unpause shown"), self.unpauseShown),
			(_("Pause all"), self.pauseAll),
			(_("Unpause all"), self.unpauseAll)],
		)

	def showHideSetTextMagic(self):
		list_type = self.list_type
		if list_type == LIST_TYPE_ALL:
			self["all_sel"].show()
			self["downloading_sel"].hide()
			self["seeding_sel"].hide()
			self["key_yellow"].setText(_("Seeding"))
			self["key_blue"].setText(_("Download"))
		elif list_type == LIST_TYPE_DOWNLOADING:
			self["all_sel"].hide()
			self["downloading_sel"].show()
			self["seeding_sel"].hide()
			self["key_yellow"].setText(_("All"))
			self["key_blue"].setText(_("Seeding"))
		else: #if list_type == LIST_TYPE_SEEDING:
			self["all_sel"].hide()
			self["downloading_sel"].hide()
			self["seeding_sel"].show()
			self["key_yellow"].setText(_("Download"))
			self["key_blue"].setText(_("All"))

	def prevlist(self):
		self.timer.stop()
		list_type = self.list_type
		if list_type == LIST_TYPE_ALL:
			self.list_type = LIST_TYPE_SEEDING
		elif list_type == LIST_TYPE_DOWNLOADING:
			self.list_type = LIST_TYPE_ALL
		else: #if list_type == LIST_TYPE_SEEDING:
			self.list_type = LIST_TYPE_DOWNLOADING
		self.showHideSetTextMagic()
		self.updateList()

	def nextlist(self):
		self.timer.stop()
		list_type = self.list_type
		if list_type == LIST_TYPE_ALL:
			self.list_type = LIST_TYPE_DOWNLOADING
		elif list_type == LIST_TYPE_DOWNLOADING:
			self.list_type = LIST_TYPE_SEEDING
		else: #if list_type == LIST_TYPE_SEEDING:
			self.list_type = LIST_TYPE_ALL
		self.showHideSetTextMagic()
		self.updateList()

	def prevItem(self):
		self['list'].selectPrevious()
		cur = self['list'].getCurrent()
		return cur and cur[0]

	def nextItem(self):
		self['list'].selectNext()
		cur = self['list'].getCurrent()
		return cur and cur[0]

	def bandwidth(self):
		reload(EmissionBandwidth)
		self.timer.stop()
		try:
			sess = self.transmission.get_session()
		except transmission.TransmissionError:
			self.session.open(
				MessageBox,
				_("Could not connect to transmission-daemon!"),
				type = MessageBox.TYPE_ERROR,
				timeout = 5
			)
			# XXX: this seems silly but cleans the gui and restarts the timer :-)
			self.updateList()
		else:
			self.session.openWithCallback(
				self.bandwidthCallback,
				EmissionBandwidth.EmissionBandwidth,
				sess,
				False
			)

	def configureCallback(self):
		self.transmission = transmission.Client(
			address = config.plugins.emission.hostname.value,
			port = config.plugins.emission.port.value,
			user = config.plugins.emission.username.value,
			password = config.plugins.emission.password.value
		)
		self.updateList()

	def updateList(self, *args, **kwargs):
		try:
			list = self.transmission.list().values()
			session = self.transmission.session_stats()
		except transmission.TransmissionError:
			# XXX: some hint in gui would be nice
			self['list'].setList([])
			self["torrents"].setText("")
			self["upspeed"].setText("")
			self["downspeed"].setText("")
		else:
			sort_type = self.sort_type
			if sort_type == SORT_TYPE_TIME:
				def cmp_func(x, y):
					x_eta = x.fields['eta']
					y_eta = y.fields['eta']
					if x_eta > -1 and y_eta < 0:
						return 1
					if x_eta < 0 and y_eta > -1:
						return -1
					# note: cmp call inversed because lower eta is "better"
					return cmp(y_eta, x_eta) or cmp(x.progress, y.progress)

				list.sort(cmp = cmp_func, reverse = True)
			elif sort_type == SORT_TYPE_PROGRESS:
				list.sort(key = lambda x: x.progress, reverse = True)
			elif sort_type == SORT_TYPE_SPEED:
				list.sort(key = lambda x: (x.rateDownload, x.rateUpload), reverse = True)
			# SORT_TYPE_ADDED is what we already have

			list_type = self.list_type
			if list_type == LIST_TYPE_ALL:
				list = [
					(x, x.name.encode('utf-8', 'ignore'),
					str(x.eta or '?:??:??').encode('utf-8'),
					int(x.progress))
					for x in list
				]
			elif list_type == LIST_TYPE_DOWNLOADING:
				list = [
					(x, x.name.encode('utf-8', 'ignore'),
					str(x.eta or '?:??:??').encode('utf-8'),
					int(x.progress))
					for x in list if x.status == "downloading"
				]
			else: #if list_type == LIST_TYPE_SEEDING:
				list = [
					(x, x.name.encode('utf-8', 'ignore'),
					str(x.eta or '?:??:??').encode('utf-8'),
					int(x.progress))
					for x in list if x.status == "seeding"
				]

			self["torrents"].setText(_("Active Torrents: %d/%d") % (session.activeTorrentCount, session.torrentCount))
			self["upspeed"].setText(_("UL: %d kb/s") % (session.uploadSpeed/1024))
			self["downspeed"].setText(_("DL: %d kb/s") % (session.downloadSpeed/1024))

			# XXX: this is a little ugly but this way we have the least
			# visible distortion :-)
			index = min(self['list'].index, len(list)-1)
			self['list'].setList(list)
			self['list'].index = index

			self.list = list
		self.timer.startLongTimer(10)

	def ok(self):
		cur = self['list'].getCurrent()
		if cur:
			reload(EmissionDetailview)
			self.timer.stop()
			self.session.openWithCallback(
				self.updateList,
				EmissionDetailview.EmissionDetailview,
				self.transmission,
				cur[0],
				self.prevItem,
				self.nextItem,
			)

	def close(self):
		self.timer.stop()
		config.plugins.emission.last_tab.value = self.list_type
		config.plugins.emission.last_tab.save()
		Screen.close(self)

__all__ = ['LIST_TYPE_ALL', 'LIST_TYPE_DOWNLOADING', \
	'LIST_TYPE_SEEDING', 'EmissionOverview', 'SORT_TYPE_TIME', \
	'SORT_TYPE_PROGRESS', 'SORT_TYPE_ADDED', 'SORT_TYPE_SPEED']


