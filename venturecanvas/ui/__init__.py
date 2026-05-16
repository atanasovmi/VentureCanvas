"""UI layer — MVC Controller and View.

* :mod:`venturecanvas.ui.controllers` is the Controller tier: one class
  per feature family (Auth, Home, Project, Collection). Controllers
  receive services via constructor injection, call them, and translate
  outcomes into NiceGUI navigation / notifications.
* :mod:`venturecanvas.ui.pages` is the View tier: the :class:`Pages`
  class binds ``@ui.page`` routes to bound methods that build NiceGUI
  components and delegate all behaviour to a controller.
"""
