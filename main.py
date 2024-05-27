import math
import sys
import os
import random
import pygame
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QScrollArea, QDialog,
                             QHBoxLayout, QRadioButton, QLineEdit, QTextEdit, QComboBox, QCheckBox,
                             QListWidget, QGroupBox, QFormLayout, QMessageBox)
from PyQt5.QtGui import QPixmap, QPalette, QBrush, QIcon
from PyQt5.QtCore import Qt, QTimer

# Главное окно приложения
class MainWindow(QWidget):
    def __init__(self, image_folder, icon_path, music_folder):
        super().__init__()
        self.image_folder = image_folder
        self.icon_path = icon_path
        self.music_folder = music_folder

        self.current_background = None
        self.is_fullscreen = True
        self.is_creating_character = False
        self.is_viewing_characters = False

        self.init_ui()
        self.init_music()

    def init_ui(self):
        self.setWindowIcon(QIcon(self.icon_path))
        self.set_random_background()
        self.create_buttons()
        self.showFullScreen()
        self.setWindowTitle("D&D character creator")

    def create_buttons(self):
        self.create_character_button = self.create_button("Создать персонажа", self.show_race_selection)
        self.view_characters_button = self.create_button("Список персонажей", self.show_character_list)
        self.exit_button = self.create_button("Выход", self.close)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.create_character_button)
        button_layout.addWidget(self.view_characters_button)
        button_layout.addWidget(self.exit_button)

        main_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        self.race_selection_widget = QWidget()
        self.class_selection_widget = QWidget()

        main_layout.addWidget(self.race_selection_widget)
        main_layout.addWidget(self.class_selection_widget)

        self.setLayout(main_layout)

    def create_button(self, text, callback):
        button = QPushButton(text, self)
        button.setFixedSize(200, 50)
        button.clicked.connect(callback)
        return button

    def set_random_background(self):
        images = [f for f in os.listdir(self.image_folder) if os.path.isfile(os.path.join(self.image_folder, f))]
        if not images:
            raise Exception("No images found in the specified directory.")
        random_image_path = os.path.join(self.image_folder, random.choice(images))
        self.current_background = QPixmap(random_image_path)
        self.update_background()

    def update_background(self):
        if self.current_background:
            scaled_pixmap = self.current_background.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            palette = QPalette()
            palette.setBrush(QPalette.Background, QBrush(scaled_pixmap))
            self.setPalette(palette)

    def show_race_selection(self):
        if not self.is_creating_character and not self.is_viewing_characters:
            self.is_creating_character = True
            self.is_viewing_characters = False
            self.hide_widget_if_exists("character_list_widget")
            self.race_selection_widget = RaceSelectionWidget(self)
            self.layout().addWidget(self.race_selection_widget)
            self.race_selection_widget.show()

    def show_character_list(self):
        if not self.is_viewing_characters and not self.is_creating_character:
            self.is_viewing_characters = True
            self.is_creating_character = False
            self.hide_widget_if_exists("race_selection_widget")
            self.character_list_widget = CharacterListWidget(self)
            self.layout().addWidget(self.character_list_widget)
            self.character_list_widget.show()

    def hide_widget_if_exists(self, widget_name):
        if hasattr(self, widget_name):
            getattr(self, widget_name).hide()

    def show_equipment_selection(self, description_window):
        self.equipment_selection_widget = EquipmentSelectionWidget(description_window)
        self.layout().addWidget(self.equipment_selection_widget)
        self.equipment_selection_widget.show()

    def show_stat_selection(self, class_selection_widget, selected_race, race_bonuses):
        self.stat_selection_widget = StatSelectionWidget(self, class_selection_widget, selected_race, race_bonuses)
        self.layout().addWidget(self.stat_selection_widget)
        self.stat_selection_widget.show()

    def show_character_description(self, selected_race, stat_selection_widget):
        self.character_description_widget = CharacterDescriptionWidget(self, selected_race, stat_selection_widget)
        self.layout().addWidget(self.character_description_widget)
        self.character_description_widget.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F10:
            if self.is_fullscreen:
                self.showNormal()
                self.is_fullscreen = False
            else:
                self.showFullScreen()
                self.is_fullscreen = True

    def resizeEvent(self, event):
        self.update_background()
        super().resizeEvent(event)

    def init_music(self):
        pygame.display.init()
        pygame.mixer.init()

        self.music_files = [f for f in os.listdir(self.music_folder)if os.path.isfile(os.path.join(self.music_folder, f))]
        if not self.music_files:
            raise Exception("No music files found in the specified directory.")
        self.play_random_music()

    def play_random_music(self):
        random_music_path = os.path.join(
            self.music_folder, random.choice(self.music_files)
        )
        pygame.mixer.music.load(random_music_path)
        pygame.mixer.music.play()
        pygame.mixer.music.set_volume(0.1)
        pygame.mixer.music.set_endevent(pygame.USEREVENT)
        self.music_timer = QTimer(self)
        self.music_timer.timeout.connect(self.check_music_end)
        self.music_timer.start(1000)

    def check_music_end(self):
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                self.play_random_music()


# Окно выбора расы
class RaceSelectionWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.selected_race = None
        self.race_bonuses = {}
        self.races = {
            "Человек": {
                "description": "Раса людей не придерживается какого-то одного ремесла, поэтому им легко в любых начинаниях",
                "features": "Дополнительный бонус +1 ко всем характеристикам.",
                "bonuses": {"Сила": 1,"Ловкость": 1,"Телосложение": 1,"Интеллект": 1,"Мудрость": 1,"Харизма": 1,},
            },
            "Драконорождённый": {
                "description": "Мистическая раса, чьё происхождение так и не было до конца раскрыто",
                "features": "Наследие дракона (Сопротивление стихии и драконье дыхание своего родителя)",
                "bonuses": {"Сила": 2, "Харизма": 1},
            },
            "Эльф": {
                "description": "Адепты лесной магии и природы. Они проворны, мудры и красноречивы",
                "features": "Темновидение, защита от очарования, магическая способность.",
                "bonuses": {"Ловкость": 2},
            },
            "Тифлинг": {
                "description": "По большей части раса людей, в чьих жилах крепко накрепко засела дьявольская кровь",
                "features": "Темновидение, сопротивление огню, дьявольское наследие (мелкое колдовство).",
                "bonuses": {"Интеллект": 1, "Харизма": 2},
            },
            "Дварф": {
                "description": "Горный народ, известный своей жадностью, огромным волосяным покровом и грубой силой",
                "features": "Темновидение, стойкость, устойчивость к ядам.",
                "bonuses": {"Телосложение": 2},
            },
            "Халфлинг": {
                "description": "Полурослики, чей род часто тратит своё свободное время на отдых и безделье. По характеру чем-то похожи на известных хоббитов",
                "features": "Темновидение, защита от испуга, ловкость рук.",
                "bonuses": {"Ловкость": 2},
            },
            "Гном": {
                "description": "Не путайте их с Дварфами. В отличие от них, Гномы живут на лугах и лесах, предпочитая грубой силе умственную работу",
                "features": "Темновидение, сопротивление магии, гномья хитрость.",
                "bonuses": {"Интеллект": 2},
            },
            "Полуэльф": {
                "description": "Полуэльфы — это смесь эльфов и людей. Они совмещают в себе магические силы и способности к адаптации, которые используют для жизни среди людей",
                "features": "Темновидение, устойчивость к очарованию, дополнительное мастерство.",
                "bonuses": {"Ловкость": 1, "Харизма": 2},
            },
            "Полуорк": {
                "description": "Сила и умение выживать унаследована от орков, а по происхождению являются смесью людей и орков",
                "features": "Темновидение, ярость, сила зверя.",
                "bonuses": {"Сила": 2, "Телосложение": 1},
            },
            "Тёмный эльф": {
                "description": "Эльфы, чьё происхождение отличается от лесных. Их далекие предки были тесно связаны с силами зла",
                "features": "Темновидение, устойчивость к огню, магическая способность.",
                "bonuses": {"Ловкость": 1, "Интеллект": 1, "Харизма": 1},
            },
        }
        self.init_ui()

    def init_ui(self):
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.display_races()

        self.next_button = QPushButton("Далее", self)
        self.exit_button = QPushButton("Выход", self)
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.proceed_to_next_step)
        self.exit_button.clicked.connect(self.close)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(self.next_button)
        main_layout.addWidget(self.exit_button)
        self.setStyleSheet("background-style:white;")
        self.setLayout(main_layout)
        QMessageBox.information(self, "Раса", "Выберите расу персонажа")

    def update_scroll_area(self):
        self.widget.setLayout(self.layout)
        self.scroll_area.setWidget(self.widget)

    def select_race(self, race_name, bonuses):
        self.selected_race = race_name
        self.race_bonuses = bonuses
        self.next_button.setEnabled(True)

    def close(self):
        self.parent.is_creating_character = False
        super().close()

    def display_races(self):
        for race_name, race_info in self.races.items():
            self.create_race_option(race_name, race_info)
        self.setStyleSheet("font-size: 16px;")
        self.update_scroll_area()

    def create_race_option(self, race_name, race_info):
        race_radio_button = QRadioButton(race_name)
        race_radio_button.clicked.connect(
            lambda _, rn=race_name, rb=race_info["bonuses"]: self.select_race(rn, rb)
        )
        self.layout.addWidget(race_radio_button)

        description_label = QLabel(race_info["description"])
        features_label = QLabel("Особенности расы: " + race_info["features"])
        bonuses_label = QLabel(
            "Дополнительные бонусы: "
            + ", ".join(
                f"{key} +{value}" for key, value in race_info["bonuses"].items()
            )
        )

        self.layout.addWidget(description_label)
        self.layout.addWidget(features_label)
        self.layout.addWidget(bonuses_label)

    def proceed_to_next_step(self):
        self.class_selection_widget = ClassSelectionWidget(
            self.parent, self.selected_race, self.race_bonuses
        )
        self.class_selection_widget.show()
        self.parent.layout().addWidget(self.class_selection_widget)
        self.hide()


# Окно выбора класса
class ClassSelectionWidget(QWidget):
    def __init__(self, parent, selected_race, race_bonuses):
        super().__init__(parent)
        self.parent = parent
        self.selected_class = None
        self.selected_race = selected_race
        self.race_bonuses = race_bonuses
        self.init_ui()

    def init_ui(self):
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.display_classes()

        self.next_button = QPushButton("Далее", self)
        self.back_button = QPushButton("Назад", self)
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.proceed_to_next_step)
        self.back_button.clicked.connect(self.return_to_previous_step)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(self.next_button)
        main_layout.addWidget(self.back_button)
        self.setStyleSheet("background-style:white;")
        self.setLayout(main_layout)
        QMessageBox.information(self, "Класс", "Выберите класс персонажа")

    def update_scroll_area(self):
        self.widget.setLayout(self.layout)
        self.scroll_area.setWidget(self.widget)

    def select_class(self, class_name):
        self.selected_class = class_name
        self.next_button.setEnabled(True)

    def display_classes(self):
        classes = {
            "Бард": "Неважно, кем является бард: учёным, скальдом или проходимцем; он плетёт магию из слов и музыки, вдохновляя союзников, деморализуя противников, манипулируя сознанием, создавая иллюзии, и даже исцеляя раны.",
            "Варвар": "Несмотря на разнообразие, всех варваров объединяет одно — их ярость. Необузданный, неугасимый и бездумный гнев. Не просто эмоция, их ярость как свирепость загнанного в угол хищника, как безжалостный удар урагана, как штормовые валы океана.",
            "Воин": "Странствующие рыцари, военачальники-завоеватели, королевские чемпионы, элитная пехота, бронированные наёмники и короли разбоя — будучи воинами, все они мастерски владеют оружием, доспехами, и приёмами ведения боя.",
            "Волшебник": "Волшебники — адепты высшей магии, объединяющиеся по типу своих заклинаний. Опираясь на тонкие плетения магии, пронизывающей вселенную, волшебники способны создавать заклинания взрывного огня, искрящихся молний, тонкого обмана и грубого контроля над сознанием.",
            "Друид": "Призывая стихии или подражая животным, друиды воплощают незыблемость, приспособляемость и гнев природы. Они ни в коем случае не владыки природы — вместо этого друиды ощущают себя частью её неодолимой воли.",
            "Жрец": "Жрецы являются посредниками между миром смертных и далёкими мирами богов. Настолько же разные, насколько боги, которым они служат, жрецы воплощают работу своих божеств.",
            "Изобретатель": "Изобретатели — величайшие мастера пробуждать магию в обычных предметах. Они рассматривают магию как сложную систему, которую следует расшифровать и применять в заклинаниях и изобретениях.",
            "Колдун": "Колдуны — искатели знаний, что скрываются в ткани мультивселенной. Через договор, заключённый с таинственными существами сверхъестественной силы, колдуны открывают для себя магические эффекты, как едва уловимые, так и впечатляющие воображение.",
            "Монах": "Вне зависимости от выбранной дисциплины, всех монахов объединяет одно — возможность управлять энергией, текущей в их телах. Вне зависимости от того, проявляется ли она выдающимися боевыми способностями, или чуть заметным усилением защиты и скорости, эта энергия влияет на всё, что делает монах.",
            "Паладин": "Вне зависимости от происхождения и миссии, паладинов объединяет их клятва противостоять силам зла. Принесённая ли перед алтарём бога и заверенная священником, или же на священной поляне перед духами природы и феями, или в момент отчаяния и горя смерти, присяга паладина — могущественный договор.",
            "Плут": "Плуты полагаются на мастерство, скрытность и уязвимые места врагов, чтобы взять верх в любой ситуации. У них достаточно сноровки для нахождения решения в любой ситуации, демонстрируя находчивость и гибкость, которые являются краеугольным камнем любой успешной группы искателей приключений.",
            "Следопыт": "Вдали от суеты городов и посёлков, за изгородями, которые защищают самые далёкие фермы от ужасов дикой природы, среди плотно стоящих деревьев, беспутья лесов и на просторах необъятных равнин следопыты несут свой бесконечный дозор.",
            "Чародей": "Чародеи являются носителями магии, дарованной им при рождении их экзотической родословной, неким потусторонним влиянием или воздействием неизвестных вселенских сил. Никто не может обучиться чародейству, как, например, выучить язык, так же как никто не может обучить, как прожить легендарную жизнь.",
        }
        for class_name, class_description in classes.items():
            self.create_class_option(class_name, class_description)
        self.setStyleSheet("font-size: 16px;")
        self.update_scroll_area()

    def create_class_option(self, class_name, class_description):
        class_radio_button = QRadioButton(class_name)
        class_radio_button.clicked.connect(
            lambda _, cn=class_name: self.select_class(cn)
        )
        self.layout.addWidget(class_radio_button)
        self.layout.addWidget(QLabel(class_description))

    def proceed_to_next_step(self):
        self.parent.show_stat_selection(self, self.selected_race, self.race_bonuses)
        self.hide()

    def return_to_previous_step(self):
        self.parent.race_selection_widget.show()
        self.hide()


# Окно распределения характеристик
class StatSelectionWidget(QWidget):
    def __init__(self, parent, class_selection_widget, selected_race, race_bonuses):
        super().__init__(parent)
        self.parent = parent
        self.class_selection_widget = class_selection_widget
        self.selected_race = selected_race
        self.stats = {
            "Сила": 0,
            "Ловкость": 0,
            "Телосложение": 0,
            "Интеллект": 0,
            "Мудрость": 0,
            "Харизма": 0,
        }
        self.selected_values = {}
        self.race_bonuses = race_bonuses
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.stat_comboboxes = {}
        self.final_stat_labels = {}

        inner_widget = QWidget()
        inner_layout = QVBoxLayout(inner_widget)
        inner_widget.setLayout(inner_layout)
        inner_widget.setStyleSheet("background-color: white;")

        for stat, bonus in self.race_bonuses.items():
            self.stats[stat] += bonus

        stat_distribution_label = QLabel(
            "Стандартное распределение характеристик: 15, 14, 13, 12, 10, 8")
        stat_distribution_label_2=QLabel("Совет: Чем выше модификатор(значение в скобках), тем лучше вы будете справляться с проверками характеристик")
        inner_layout.addWidget(stat_distribution_label)
        inner_layout.addWidget(stat_distribution_label_2)

        for stat in self.stats.keys():
            h_layout = QHBoxLayout()
            stat_label = QLabel(
                f"{stat} (бонус от расы: +{self.race_bonuses.get(stat, 0)})"
            )
            stat_combobox = QComboBox()
            stat_combobox.addItems(["15", "14", "13", "12", "10", "8", "0"])
            stat_combobox.setCurrentIndex(6)
            stat_combobox.currentIndexChanged.connect(
                lambda _, s=stat, cb=stat_combobox: self.update_stat(
                    s, cb.currentText()
                )
            )
            h_layout.addWidget(stat_label)
            h_layout.addWidget(stat_combobox)
            self.stat_comboboxes[stat] = stat_combobox

            final_stat_label = QLabel(
                f"Итоговое значение и модификатор: {self.stats[stat]} ({math.floor((self.stats[stat] - 10) / 2)})"
            )
            self.final_stat_labels[stat] = final_stat_label
            h_layout.addWidget(final_stat_label)

            inner_layout.addLayout(h_layout)

        self.next_button = QPushButton("Далее", self)
        self.back_button = QPushButton("Назад", self)
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.proceed_to_next_step)
        self.back_button.clicked.connect(self.return_to_previous_step)

        inner_layout.addWidget(self.next_button)
        inner_layout.addWidget(self.back_button)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(inner_widget)

        self.layout.addWidget(self.scroll_area)
        self.setStyleSheet("font-size: 16px;")
        self.setLayout(self.layout)
        QMessageBox.information(
            self, "Характеристики", "Распределите характеристики персонажа"
        )

    def update_stat(self, stat, value):
        if value and value != "0":
            self.selected_values[stat] = value
        else:
            self.selected_values.pop(stat, None)

        self.stats[stat] = (
            int(value) + self.race_bonuses.get(stat, 0) if value != "0" else 0
        )
        modifier = math.floor((self.stats[stat] - 10) / 2)
        self.final_stat_labels[stat].setText(
            f"Итоговое значение и модификатор: {self.stats[stat]} ({modifier})"
        )
        self.update_comboboxes()

        self.next_button.setEnabled(len(self.selected_values) == len(self.stats))

    def update_comboboxes(self):
        all_values = {"0", "15", "14", "13", "12", "10", "8"}
        used_values = set(self.selected_values.values())

        for stat, combobox in self.stat_comboboxes.items():
            current_value = combobox.currentText()

            combobox.blockSignals(True)
            combobox.clear()
            for value in sorted(all_values, key=int, reverse=True):
                if value == current_value or value not in used_values:
                    combobox.addItem(value)

            combobox.setCurrentText(
                current_value if current_value in all_values else "0"
            )
            combobox.blockSignals(False)

    def proceed_to_next_step(self):
        self.parent.race_bonuses = self.race_bonuses
        self.parent.show_character_description(self.selected_race, self)
        self.hide()

    def return_to_previous_step(self):
        self.class_selection_widget.show()
        self.hide()


# Окно описания персонажа
class CharacterDescriptionWidget(QDialog):
    def __init__(self, parent, selected_race, stat_selection_widget):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(276, 76, 1555, 922)
        self.character_description = ""
        self.character_name = ""
        self.selected_race = selected_race
        self.stat_selection_widget = stat_selection_widget
        self.race_bonuses = parent.race_bonuses
        self.class_selection_widget = (
            parent.stat_selection_widget.class_selection_widget
        )
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        name_label = QLabel("Введите имя персонажа:")
        name_label.setStyleSheet("background-color: white; font-size: 16px;")
        layout.addWidget(name_label)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.check_input)
        layout.addWidget(self.name_edit)

        description_label = QLabel("Описание персонажа:")
        description_label.setStyleSheet("background-color: white; font-size: 16px;")
        layout.addWidget(description_label)

        self.description_edit = QTextEdit()
        layout.addWidget(self.description_edit)

        self.next_button = QPushButton("Далее", self)
        self.next_button.setEnabled(False)
        self.back_button = QPushButton("Назад", self)
        self.next_button.clicked.connect(self.proceed_to_next_step)
        self.back_button.clicked.connect(self.return_to_previous_step)

        layout.addWidget(self.next_button)
        layout.addWidget(self.back_button)
        self.setStyleSheet("background-style:white;")
        self.setStyleSheet("font-size: 16px;")
        self.setLayout(layout)
        QMessageBox.information(self, "Описание", "Введите Имя и описание персонажа")

    def check_input(self):
        self.next_button.setEnabled(bool(self.name_edit.text().strip()))

    def proceed_to_next_step(self):
        self.character_name = self.name_edit.text().strip()
        self.character_description = self.description_edit.toPlainText().strip()
        if not self.character_name:
            QMessageBox.warning(self, "Ошибка", "Имя персонажа не может быть пустым.")
            return
        self.parent().show_equipment_selection(self)
        self.hide()

    def return_to_previous_step(self):
        if self.stat_selection_widget:
            self.stat_selection_widget.show()
        self.parent().is_creating_character = False
        self.close()


# Окно выбора снаряжения
class EquipmentSelectionWidget(QDialog):
    def __init__(self, description_window):
        super().__init__(description_window)
        self.setWindowTitle("Выбор снаряжения")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(276, 76, 1555, 922)
        self.description_window = description_window
        self.selected_equipment = {
            "оружие": None,
            "снаряжение": None,
            "инструменты": None,
            "снаряжение класса": None,
        }
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        class_name = self.description_window.class_selection_widget.selected_class

        equipment = {
            "Бард": {
                "оружие": ["Рапира", "Длинный меч", "Кинжал"],
                "снаряжение": ["Кожаная броня", "Мантия"],
                "инструменты": ["Набор артиста", "Набор дипломата", "Набор книг"],
                "снаряжение класса": ["Лютня", "Флейта", "Скрипка"],
            },
            "Варвар": {
                "оружие": ["Секира", "Молот", "Два ручных топора"],
                "снаряжение": ["Кожаная броня", "Кольчуга", "Обмотки"],
                "инструменты": ["Набор путешественника"],
                "снаряжение класса": ["Боевой рог"],
            },
            "Воин": {
                "оружие": ["Двуручный меч", "Длинный меч", "Длинный лук"],
                "снаряжение": ["Кожаная броня", "Кольчуга"],
                "инструменты": [
                    "Набор путешественника",
                    "Набор исследователя подземелий",
                ],
                "снаряжение класса": [],
            },
            "Волшебник": {
                "оружие": ["Посох", "Кинжал"],
                "снаряжение": ["Мантия"],
                "инструменты": ["Набор учёного", "Мешочек с компонентами"],
                "снаряжение класса": ["Книга заклинаний"],
            },
            "Друид": {
                "оружие": ["Боевой", "Скимитар"],
                "снаряжение": ["Кожаная броня", "Тканный доспех"],
                "инструменты": ["Набор путешественника"],
                "снаряжение класса": ["Посох друида"],
            },
            "Жрец": {
                "оружие": ["Булава", "Боевой молот"],
                "снаряжение": ["Чешуйчатый доспех", "Кольчуга", "Кожаный доспех"],
                "инструменты": ["Набор путешественника", "Набор священника"],
                "снаряжение класса": ["Священный символ и щит церкви"],
            },
            "Изобретатель": {
                "оружие": ["Меч", "Лёгкий арбалет"],
                "снаряжение": ["Поклёпанная броня", "Чешуйчатый доспех"],
                "инструменты": [
                    "Воровские инструменты",
                    "Набор исследователя подземелий",
                ],
                "снаряжение класса": ["Однозарядный пистолет"],
            },
            "Колдун": {
                "оружие": ["Короткий меч", "Лёгкий арбалет"],
                "снаряжение": ["Кожаная броня"],
                "инструменты": [
                    "Набор учёного",
                    "Набор исследователя подземелий",
                    "Мешочек с компонентами",
                ],
                "снаряжение класса": ["Гримуар"],
            },
            "Монах": {
                "оружие": ["Боевой посохч", "Короткий меч"],
                "снаряжение": ["Обмотки"],
                "инструменты": [
                    "Набор путешественника",
                    "Набор исследователя подземелий",
                ],
                "снаряжение класса": ["Чётки для ци"],
            },
            "Паладин": {
                "оружие": ["Двуручный меч", "Боевой молот"],
                "снаряжение": ["Кольчуга", "Латные доспехи"],
                "инструменты": ["Набор путешественника", "Набор священника"],
                "снаряжение класса": ["Священный символ"],
            },
            "Плут": {
                "оружие": ["Рапира", "Короткий меч"],
                "снаряжение": ["Кожаный доспех с капюшоном"],
                "инструменты": [
                    "Набор взломщика",
                    "Набор исследователя подземелий",
                    "Набор путешественника",
                ],
                "снаряжение класса": ["Кинжалы"],
            },
            "Следопыт": {
                "оружие": ["Два скимитара", "Два коротких меча"],
                "снаряжение": ["Кожаная броня", "Чешуйчатый доспех"],
                "инструменты": [
                    "Набор путешественника",
                    "Набор исследователя подземелий",
                ],
                "снаряжение класса": ["Длинный лук"],
            },
            "Чародей": {
                "оружие": ["Два кинжала", "Короткий меч"],
                "снаряжение": ["Мантия"],
                "инструменты": [
                    "Набор путешественника",
                    "Набор исследователя подземелий",
                    "Мешочек с компонентами",
                ],
                "снаряжение класса": ["Магическая семейная реликвия"],
            },
        }

        equipment_label = QLabel(f"Выберите снаряжение для класса: {class_name}")
        equipment_label.setStyleSheet("background-color: white;font-size:16px;")
        layout.addWidget(equipment_label)

        self.equipment_checkboxes = {
            "оружие": [],
            "снаряжение": [],
            "инструменты": [],
            "снаряжение класса": [],
        }

        for category, items in equipment[class_name].items():
            layout.addWidget(self.create_equipment_groupbox(category, items))

        self.finish_button = QPushButton("Закончить", self)
        self.back_button = QPushButton("Назад", self)
        self.finish_button.clicked.connect(self.finish_creation)
        self.back_button.clicked.connect(self.return_to_previous_step)

        layout.addWidget(self.finish_button)
        layout.addWidget(self.back_button)
        self.setStyleSheet("background-color: white; font-size: 16px;")
        self.setLayout(layout)
        QMessageBox.information(
            self,
            "Снаряжение",
            "Выберите снаряжение персонажа (По одному предмету каждого типа)",
        )

    def create_equipment_groupbox(self, title, items):
        groupbox = QGroupBox(title)
        form_layout = QFormLayout()
        for item in items:
            checkbox = QCheckBox(item)
            checkbox.stateChanged.connect(
                lambda state, cb=checkbox, cat=title: self.update_equipment_selection(
                    cat, cb
                )
            )
            form_layout.addRow(checkbox)
            self.equipment_checkboxes[title].append(checkbox)
        groupbox.setLayout(form_layout)
        groupbox.setStyleSheet("background-color: white;")
        return groupbox

    def update_equipment_selection(self, category, checkbox):
        if checkbox.isChecked():
            for cb in self.equipment_checkboxes[category]:
                if cb != checkbox:
                    cb.setEnabled(False)
            self.selected_equipment[category] = checkbox.text()
        else:
            for cb in self.equipment_checkboxes[category]:
                cb.setEnabled(True)
            self.selected_equipment[category] = None

    def finish_creation(self):
        selected_race = self.description_window.selected_race
        race_features = self.description_window.parent().race_selection_widget.races[
            selected_race
        ]["features"]

        character_data = {
            "Имя": self.description_window.character_name,
            "Раса": selected_race,
            "Класс": self.description_window.class_selection_widget.selected_class,
            "Описание": self.description_window.character_description,
            "Снаряжение": self.selected_equipment,
            "Особенности расы": race_features,
        }

        stats_and_modifiers = self.description_window.stat_selection_widget.stats
        for stat, value in stats_and_modifiers.items():
            character_data[f"{stat}"] = f"{value} ({math.floor((value - 10) / 2)})"

        if not os.path.exists("characters"):
            os.makedirs("characters")
        file_path = os.path.join("characters", f"{character_data['Имя']}.txt")
        with open(file_path, "w") as file:
            for key, value in character_data.items():
                file.write(f"{key}: {value}\n")
        QMessageBox.information(
            self,
            "Сохранение персонажа",
            f"Персонаж '{self.description_window.character_name}' успешно создан и сохранен!",
        )
        self.description_window.parent().is_creating_character = False
        self.close()

    def return_to_previous_step(self):
        self.description_window.show()
        self.close()


# Вызов списка персонажей
class CharacterListWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Список персонажей")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(276, 76, 1555, 922)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.character_list = QListWidget()
        self.character_list.itemClicked.connect(self.display_character_info)

        self.load_characters()

        layout.addWidget(self.character_list)

        self.delete_button = QPushButton("Удалить", self)
        self.delete_button.clicked.connect(self.delete_character)
        layout.addWidget(self.delete_button)

        self.back_button = QPushButton("Назад", self)
        self.back_button.clicked.connect(self.return_to_main_menu)
        layout.addWidget(self.back_button)

        self.character_info_text = QTextEdit()
        self.character_info_text.setReadOnly(True)
        layout.addWidget(self.character_info_text)

        self.setLayout(layout)

    def load_characters(self):
        if not os.path.exists("characters"):
            os.makedirs("characters")
        for character_file in os.listdir("characters"):
            if character_file.endswith(".txt"):
                self.character_list.addItem(character_file.replace(".txt", ""))

    def display_character_info(self, item):
        character_name = item.text()
        file_path = os.path.join("characters", f"{character_name}.txt")
        with open(file_path, "r") as file:
            character_info = file.read()
        self.character_info_text.setStyleSheet("font-size: 16px;")
        self.character_info_text.setText(character_info)

    def delete_character(self):
        current_item = self.character_list.currentItem()
        if current_item:
            character_name = current_item.text()
            file_path = os.path.join("characters", f"{character_name}.txt")
            os.remove(file_path)
            self.character_list.takeItem(self.character_list.row(current_item))
            self.character_info_text.clear()

    def return_to_main_menu(self):
        self.hide()
        self.parent.is_viewing_characters = False
        self.parent.show()


# Начало программы
if __name__ == "__main__":
    app = QApplication(sys.argv)
    image_folder = "Pictures/Background"
    icon_path = "Pictures/Icon/D&D.ico"
    music_folder = "Music"
    main_window = MainWindow(image_folder, icon_path, music_folder)
    main_window.show()
    sys.exit(app.exec_())
