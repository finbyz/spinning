#import frappe

def before_cancel(self,method):
    self.flags.ignore_links = True