STYLE = """
* { font-family: 'Segoe UI'; font-size: 10pt; color: #26283d; }
QMainWindow, QDialog { background: #f8f9fc; }
QWidget#sidebar { background: #f0f1f7; border-right: 1px solid #e1e4ef; }
QWidget#canvas { background: #f8f9fc; }
QLabel#brand { font-size: 25pt; font-weight: 700; letter-spacing: -1px; }
QLabel#eyebrow { font-size: 9pt; color: #737991; font-weight: 600; }
QLabel#heading { font-size: 25pt; font-weight: 650; letter-spacing: -1px; }
QLabel#subheading { font-size: 15pt; font-weight: 600; }
QLabel#muted { color: #747b91; }
QLabel#badge { color: #286857; background: #e6f2ec; padding: 6px 12px; border-radius: 12px; font-size: 9pt; }
QLabel#error { color: #923c47; background: #fff0f1; padding: 12px; border: 1px solid #f3d7db; border-radius: 8px; }
QFrame#card { background: white; border: 1px solid #e2e5ef; border-radius: 12px; }
QFrame#card QLabel { background: transparent; border: none; }
QPushButton { background: white; border: 1px solid #dce0eb; border-radius: 7px; padding: 10px 16px; font-weight: 600; }
QPushButton:hover { background: #f0f0fc; border-color: #a6a8df; }
QPushButton:pressed { background: #e5e5f7; }
QPushButton:focus { border: 2px solid #8584da; }
QPushButton:disabled { background: #f2f3f7; color: #9ba0b1; border-color: #e6e8ef; }
QPushButton#primary { background: #5b57d6; color: white; border: 1px solid #5b57d6; }
QPushButton#primary:hover { background: #4945bf; }
QPushButton#primary:pressed { background: #39369e; }
QPushButton#primary:disabled { background: #c1bfe9; color: #f5f5fc; border-color: #c1bfe9; }
QPushButton#danger { background: #b5495b; color: white; border-color: #b5495b; }
QPushButton#quiet { background: transparent; color: #61657e; border: none; text-align: left; }
QLineEdit, QComboBox { background: white; border: 1px solid #dce0eb; border-radius: 6px; padding: 9px; selection-background-color: #5b57d6; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #7572d7; }
QListWidget { background: transparent; border: none; outline: none; }
QListWidget::item { border-radius: 7px; padding: 12px 10px; margin: 2px 0; color: #60667d; }
QListWidget::item:selected { background: #e1e1f4; color: #4541af; }
QListWidget::item:hover { background: #e8eaf3; }
QTabWidget::pane { border: none; }
QTabBar::tab { background: transparent; padding: 13px 21px; color: #777d92; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #534fc2; border-bottom: 2px solid #5b57d6; }
QTabBar::tab:disabled { color: #a7abba; }
QScrollArea { background: transparent; border: none; }
QTableWidget { background: white; border: 1px solid #e2e5ef; border-radius: 8px; gridline-color: #eef0f6; selection-background-color: #efeffa; selection-color: #26283d; }
QHeaderView::section { background: #f4f5f9; border: none; border-bottom: 1px solid #e2e5ef; padding: 12px; color: #747b91; font-weight: 600; }
QTableWidget::item { padding: 9px; }
QProgressBar { background: #e6e7f2; border: none; border-radius: 3px; max-height: 6px; min-height: 6px; }
QProgressBar::chunk { background: #7975df; border-radius: 3px; }
QSlider::groove:horizontal { height: 4px; background: #e2e4ef; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #7975df; border-radius: 2px; }
QSlider::handle:horizontal { width: 12px; height: 12px; margin: -4px 0; background: #5b57d6; border-radius: 6px; }
QTextEdit { background: white; border: 1px solid #e2e5ef; border-radius: 6px; padding: 8px; }
QToolTip { background: #26283d; color: white; border: none; padding: 7px; }
"""
