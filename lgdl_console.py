from libgen_dl import LibgenSession, LibgenBook
import npyscreen


"""
FORMS
"""

# Welcome screen
class welcomeForm(npyscreen.Form):
    """
    This is the first form displayed. It contains all of the options
    for navigating the rest of the application.
    """

    # Set up the form
    def create(self):
        self.add(npyscreen.Title)

# # Wrapper for curses init and the application forms
# class LibgenDLApp(npyscreen.NPSAppManaged):
#     def onStart(self):
#         self.registerForm("MAIN", MainForm())
#
#
# # Main display
# class MainForm(npyscreen.Form):
#     def create(self):
#         self.add(npyscreen.TitleText, name="Text:", value="Hello World!")
#
#     def afterEditing(self):
#         self.parentApp.setNextForm(None)
#
#
# # Run
# if __name__ == '__main__':
#     LGDLA = LibgenDLApp()
#     LGDLA.run()
#
# DEPTS = ['Executive', 'HR', 'Accounting', 'IT']
#
#
# class MyEmployeeForm(npyscreen.Form):
#     def create(self):
#         self.myName = self.add(npyscreen.TitleText, name='Name')
#         self.myDept = self.add(npyscreen.TitleSelectOne, scroll_exit=True, max_height=len(DEPTS), values=DEPTS, name='Department')
#         self.myDate = self.add(npyscreen.TitleDateCombo, name='Date Employed')
#
#     def afterEditing(self):
#         self.parentApp.setNextForm(None)
#
#
# class MyApplication(npyscreen.NPSAppManaged):
#     def onStart(self):
#         self.addForm('MAIN', MyEmployeeForm, name='New Employee')
#
# if __name__ == '__main__':
#     TestApp = MyApplication().run()
#     print("All objects, baby")