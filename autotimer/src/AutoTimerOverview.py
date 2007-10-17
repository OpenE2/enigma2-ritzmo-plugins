# GUI (Screens)
from Screens.Screen import Screen
from AutoTimerEditor import AutoTimerEditor

# GUI (Components)
from AutoTimerList import AutoTimerList
from Components.ActionMap import ActionMap
from Components.Button import Button

# Plugin
from AutoTimerComponent import AutoTimerComponent

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
		try:
			self.autotimer.readXml()
		except:
			# Don't crash during development
			import traceback, sys
			traceback.print_exc(file=sys.stdout)

		# Button Labels
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button(_("Delete"))
		self["key_blue"] = Button(_("Add"))

		# Create List of Timers
		self["entries"] = AutoTimerList(autotimer.getTupleTimerList())

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
			self.addCallback,
			AutoTimerEditor,
			# TODO: implement setting a default?
			AutoTimerComponent(
				self.autotimer.getUniqueId(),	# Id
				"",								# Name
				True							# Enabled				
			)
		)

	def addCallback(self, ret):
		if ret:
			self.autotimer.set(ret)
			self.refresh()

	def refresh(self, res = None):
		# Re-assign List
		self["entries"].setList(self.autotimer.getTupleTimerList())

	def ok(self):
		# Edit selected Timer
		current = self["entries"].getCurrent()
		if current is not None:
			self.session.openWithCallback(
				self.refresh,
				AutoTimerEditor,
				current[0]
			)

	def remove(self):
		# Remove selected Timer
		current = self["entries"].getCurrent()
		if current is not None:
			self.autotimer.remove(current[0].id)
			self.refresh()

	def cancel(self):
		self.close(None)

	def save(self):
		# Save Xml
		try:
			self.autotimer.writeXml()
		except:
			# Don't crash during development
			import traceback, sys
			traceback.print_exc(file=sys.stdout)

		# Nothing else to be done?
		self.close(self.session)