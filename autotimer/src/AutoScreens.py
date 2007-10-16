# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Screens.ChannelSelection import SimpleChannelSelection

# GUI (Components)
from AutoList import AutoList
from Components.ActionMap import ActionMap
from Components.Button import Button

# Configuration
from Components.config import getConfigListEntry, ConfigEnableDisable, ConfigText, ConfigClock, ConfigInteger, ConfigSelection

# Timer
from RecordTimer import AFTEREVENT

class AutoChannelEdit(Screen, ConfigListScreen):
	skin = """<screen name="AutoChannelEdit" title="Edit AutoTimer Channels" position="75,150" size="560,240">
		<widget name="config" position="0,0" size="560,200" scrollbarMode="showOnDemand" />
		<ePixmap position="0,200" zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,200" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,200" zPosition="4" size="140,40" pixmap="skin_default/key-yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,200" zPosition="4" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,200" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,200" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="280,200" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="420,200" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, servicerestriction, servicelist):
		Screen.__init__(self, session)

		self.list = [
			getConfigListEntry("Enable Channel Restriction", ConfigEnableDisable(default = servicerestriction))
		]

		#
		# TODO
		# FIXME
		# WARNING
		#
		# We're using ConfigText here because we can't give ConfigNothin a value
		# and there is no other uneditable element - you better not break the
		# ServiceRef (by accident) ;)
		#
		# I'd actually like to show ServiceName instead of ServiceRef but did not
		# come up with a solution for this yet.
		#
		self.list.extend([
			getConfigListEntry("Allowed Channel", ConfigText(default = x, fixed_size= True))
				for x in servicelist
		])

		ConfigListScreen.__init__(self, self.list, session = session)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button(_("delete"))
		self["key_blue"] = Button(_("New"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"yellow": self.removeChannel,
				"blue": self.newChannel
			}
		)

	def removeChannel(self):
		if self["config"].getCurrentIndex() != 0:
			list = self["config"].getList()
			list.remove(self["config"].getCurrent())
			self["config"].setList(list)

	def newChannel(self):
		self.session.openWithCallback(
			self.finishedChannelSelection,
			SimpleChannelSelection,
			_("Select channel to record from")
		)

	def finishedChannelSelection(self, *args):
		if len(args):
			list = self["config"].getList()
			list.append(getConfigListEntry("Allowed Channel", ConfigText(default = args[0].toString().encode('UTF-8'), fixed_size= True)))
			self["config"].setList(list)

	def cancel(self):
		self.close(None)

	def save(self):
		list = self["config"].getList()
		restriction = list.pop(0)

		# Warning, accessing a ConfigListEntry directly might be considered evil!
		self.close((
			restriction[1].value,
			[
				x[1].value
					for x in list
			]
		))

class AutoTimerEdit(Screen, ConfigListScreen):
	skin = """<screen name="AutoTimerEdit" title="Edit AutoTimer" position="130,150" size="450,240">
		<widget name="config" position="0,0" size="450,200" scrollbarMode="showOnDemand" />
		<ePixmap position="0,200" zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,200" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
		<ePixmap position="310,200" zPosition="4" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,200" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,200" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="310,200" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session, timertuple):
		Screen.__init__(self, session)

		# We need to keep our Id
		self.uniqueTimerId = timertuple[0]

		# TODO: implement configuration for these - for now we just keep them
		self.excludes = timertuple[6]
		self.maxduration = timertuple[7]

		# See if services are restricted
		if timertuple[3] is None:
			self.serviceRestriction = False
			self.services = []
		else:
			self.serviceRestriction = True
			self.services = timertuple[3]

		self.createSetup(timertuple)

		# We might need to change shown items, so add some notifiers
		self.timespan.addNotifier(self.reloadList, initial_call = False)
		self.offset.addNotifier(self.reloadList, initial_call = False)

		self.refresh()

		ConfigListScreen.__init__(self, self.list, session = session)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_blue"] = Button(_("Edit Channels"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"save": self.save,
				"blue": self.editChannels
			}
		)

	def createSetup(self, timertuple):
		# Name
		self.name = ConfigText(default = timertuple[1], fixed_size = False)

		# Timespan
		if timertuple[2] is not None:
			default = True
			begin = timertuple[2][0][0] * 3600 + timertuple[2][0][1] * 60 
			end = timertuple[2][1][0] * 3600 + timertuple[2][1][1] * 60
		else:
			default = False
			begin = 72900	# 20:15
			end = 83700		# 23:15
		self.timespan = ConfigEnableDisable(default = default)
		self.timespanbegin = ConfigClock(default = begin)
		self.timespanend = ConfigClock(default = end)

		# Services have their own Screen

		# Offset
		if timertuple[4] is not None:
			default = True
			begin = timertuple[4][0] / 60
			end = timertuple[4][1] / 60
		else:
			default = False
			begin = 5
			end = 5
		self.offset = ConfigEnableDisable(default = default)
		self.offsetbegin = ConfigInteger(default = begin, limits = (0, 60))
		self.offsetend = ConfigInteger(default = end, limits = (0, 60))

		# AfterEvent
		afterevent = { AFTEREVENT.NONE: "nothing", AFTEREVENT.DEEPSTANDBY: "deepstandby", AFTEREVENT.STANDBY: "standby"}[timertuple[5]]
		self.afterevent = ConfigSelection(choices = [("nothing", _("do nothing")), ("standby", _("go to standby")), ("deepstandby", _("go to deep standby"))], default = afterevent)

	def refresh(self):
		# First two entries are always shown
		self.list = [
			getConfigListEntry("Match Title", self.name),
			getConfigListEntry("Only match during Timespan", self.timespan)
		]

		# Only allow editing timespan when it's enabled
		if self.timespan.value:
			self.list.extend([
				getConfigListEntry("Begin of Timespan", self.timespanbegin),
				getConfigListEntry("End of Timespan", self.timespanend)
			])

		self.list.append(getConfigListEntry("Custom offset", self.offset))

		# Only allow editing offsets when it's enabled
		if self.offset.value:
			self.list.extend([
				getConfigListEntry("Offset before recording (in m)", self.offsetbegin),
				getConfigListEntry("Offset after recording (in m)", self.offsetend)
			])

		self.list.append(getConfigListEntry(_("After event"), self.afterevent))

	def reloadList(self, value):
		self.refresh()
		self["config"].setList(self.list)

	def editChannels(self):
		self.session.openWithCallback(
			self.editCallback,
			AutoChannelEdit,
			self.serviceRestriction,
			self.services
		)

	def editCallback(self, ret):
		if ret:
			self.serviceRestriction = ret[0]
			self.services = ret[1] 

	def cancel(self):
		self.close(None)

	def save(self):
		# Create new tuple

		# Timespan
		if self.timespan.value:
			start = self.timespanbegin.value
			end = self.timespanend.value
			if end[0] < start[0] or (end[0] == start[0] and end[1] <= start[1]):
				haveDayspan = True
			else:	
				haveDayspan = False
			timetuple = (start, end, haveDayspan)
		else:
			timetuple= None

		# Services
		if self.serviceRestriction:
			servicelist = self.services
		else:
			servicelist = None

		# Offset
		if self.offset.value:
			offset = (self.offsetbegin.value*60, self.offsetend.value*60)
		else:
			offset = None

		# AfterEvent
		afterevent = {"nothing": AFTEREVENT.NONE, "deepstandby": AFTEREVENT.DEEPSTANDBY, "standby": AFTEREVENT.STANDBY}[self.afterevent.value]

		# Close and return tuple
		self.close((
			self.uniqueTimerId,
			self.name.value,
			timetuple,
			servicelist,
			offset,
			afterevent,
			self.excludes,
			self.maxduration
		))

class AutoTimerOverview(Screen):
	skin = """
		<screen name="AutoTimerOverview" position="140,148" size="420,250" title="AutoTimer Overview">
			<widget name="entries" position="5,0" size="410,200" scrollbarMode="showOnDemand" />
			<ePixmap position="0,205" zPosition="1" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
			<ePixmap position="140,205" zPosition="1" size="140,40" pixmap="skin_default/key-yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="280,205" zPosition="1" size="140,40" pixmap="skin_default/key-blue.png" transparent="1" alphatest="on" />
			<widget name="key_green" position="0,205" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="140,205" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="280,205" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" transparent="1" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, autotimer):
		Screen.__init__(self, session)

		# Save autotimer and read in Xml
		self.autotimer = autotimer
		autotimer.readXml()

		# Button Labels
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button(_("Delete"))
		self["key_blue"] = Button(_("Add"))

		# Create List of Timers
		self["entries"] = AutoList(autotimer.getTimerList())

		# Define Actions
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"ok": self.ok,
				"cancel": self.cancel,
				"green": self.save,
				"yellow": self.remove,
				"blue": self.add
			}
		)

	def add(self):
		self.session.openWithCallback(
			self.editCallback,
			AutoTimerEdit,
			# TODO: implement setting a default?
			(
				self.autotimer.getUniqueId(),	# Id
				"",								# Name
				None,							# Timespan
				None,							# Services
				None,							# Offset
				AFTEREVENT.NONE,				# AfterEvent
				None,							# Excludes
				None							# Maxlength
			)
		)

	def refresh(self):
		# Re-assign List
		self["entries"].setList(self.autotimer.getTimerList())

	def ok(self):
		# Edit selected Timer
		current = self["entries"].getCurrent()
		if current is not None:
			self.session.openWithCallback(
				self.editCallback,
				AutoTimerEdit,
				current
			)

	def editCallback(self, res):
		if res is not None:
			self.autotimer.set(res)
			self.refresh()

	def remove(self):
		# Remove selected Timer
		current = self["entries"].getCurrent()
		if current is not None:
			self.autotimer.remove(current[0])
			self.refresh()

	def cancel(self):
		self.close(None)

	def save(self):
		# Save Xml
		self.autotimer.writeXml()

		# Nothing else to be done?
		self.close(self.session)