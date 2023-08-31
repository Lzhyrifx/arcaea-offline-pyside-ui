from enum import IntEnum
from typing import Any, Optional

from arcaea_offline.calculate import calculate_score_range
from arcaea_offline.models import Chart, Score
from PySide6.QtCore import QCoreApplication, QDateTime, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QWidget,
)

from ui.designer.components.scoreEditor_ui import Ui_ScoreEditor


class ScoreValidateResult(IntEnum):
    Ok = 0
    ScoreMismatch = 1
    ScoreEmpty = 2
    ChartInvalid = 50
    ScoreIncomplete = 100


class ScoreEditor(Ui_ScoreEditor, QWidget):
    valueChanged = Signal()
    accepted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.__validateBeforeAccept = True
        self.__chart = None
        self.__score_id = None

        self.scoreLineEdit.textChanged.connect(self.valueChanged)
        self.pureSpinBox.valueChanged.connect(self.valueChanged)
        self.farSpinBox.valueChanged.connect(self.valueChanged)
        self.lostSpinBox.valueChanged.connect(self.valueChanged)
        self.dateTimeEdit.dateTimeChanged.connect(self.valueChanged)
        self.maxRecallSpinBox.valueChanged.connect(self.valueChanged)
        self.modifierComboBox.currentIndexChanged.connect(self.valueChanged)
        self.clearTypeComboBox.currentIndexChanged.connect(self.valueChanged)
        self.commentLineEdit.textChanged.connect(self.valueChanged)
        self.pureNoneCheckBox.toggled.connect(self.valueChanged)
        self.farNoneCheckBox.toggled.connect(self.valueChanged)
        self.lostNoneCheckBox.toggled.connect(self.valueChanged)
        self.dateNoneCheckBox.toggled.connect(self.valueChanged)
        self.maxRecallNoneCheckBox.toggled.connect(self.valueChanged)
        self.modifierNoneCheckBox.toggled.connect(self.valueChanged)
        self.clearTypeNoneCheckBox.toggled.connect(self.valueChanged)
        self.commentNoneCheckBox.toggled.connect(self.valueChanged)
        self.valueChanged.connect(self.validateScore)
        self.valueChanged.connect(self.updateValidateLabel)

        self.modifierComboBox.addItem("NORMAL", 0)
        self.modifierComboBox.addItem("EASY", 1)
        self.modifierComboBox.addItem("HARD", 2)
        self.modifierComboBox.setCurrentIndex(-1)
        self.clearTypeComboBox.addItem("TRACK LOST", 0)
        self.clearTypeComboBox.addItem("NORMAL CLEAR", 1)
        self.clearTypeComboBox.addItem("FULL RECALL", 2)
        self.clearTypeComboBox.addItem("PURE MEMORY", 3)
        self.clearTypeComboBox.addItem("EASY CLEAR", 4)
        self.clearTypeComboBox.addItem("HARD CLEAR", 5)
        self.clearTypeComboBox.setCurrentIndex(-1)

        self.dateTimeEdit.setDateTime(QDateTime.currentDateTime())

    def setValidateBeforeAccept(self, __bool: bool):
        self.__validateBeforeAccept = __bool

    def triggerValidateMessageBox(self):
        validate = self.validateScore()

        if validate in [ScoreValidateResult.Ok, ScoreValidateResult.ScoreIncomplete]:
            return True
        if validate == ScoreValidateResult.ChartInvalid:
            QMessageBox.critical(
                self,
                # fmt: off
                QCoreApplication.translate("ScoreEditor", "chartInvalidDialog.title"),
                QCoreApplication.translate("ScoreEditor", "chartInvalidDialog.title"),
                # fmt: on
            )
            return False
        if validate == ScoreValidateResult.ScoreMismatch:
            result = QMessageBox.warning(
                self,
                # fmt: off
                QCoreApplication.translate("ScoreEditor", "scoreMismatchDialog.title"),
                QCoreApplication.translate("ScoreEditor", "scoreMismatchDialog.content"),
                # fmt: on
                QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.No,
            )
            return result == QMessageBox.StandardButton.Yes
        elif validate == ScoreValidateResult.ScoreEmpty:
            result = QMessageBox.warning(
                self,
                # fmt: off
                QCoreApplication.translate("ScoreEditor", "emptyScoreDialog.title"),
                QCoreApplication.translate("ScoreEditor", "emptyScoreDialog.content"),
                # fmt: on
                QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.No,
            )
            return result == QMessageBox.StandardButton.Yes
        else:
            return False

    @Slot()
    def on_commitButton_clicked(self):
        userAccept = (
            self.triggerValidateMessageBox() if self.__validateBeforeAccept else True
        )

        if userAccept:
            self.accepted.emit()

    def score(self):
        score_text = self.scoreLineEdit.text().replace("'", "")
        return int(score_text) if score_text else 0

    def setMinimums(self):
        self.pureSpinBox.setMinimum(0)
        self.farSpinBox.setMinimum(0)
        self.lostSpinBox.setMinimum(0)
        self.maxRecallSpinBox.setMinimum(-1)

    def setLimits(self, chart: Chart):
        self.setMinimums()
        self.pureSpinBox.setMaximum(chart.notes)
        self.farSpinBox.setMaximum(chart.notes)
        self.lostSpinBox.setMaximum(chart.notes)
        self.maxRecallSpinBox.setMaximum(chart.notes)

    def resetLimits(self):
        self.setMinimums()
        self.pureSpinBox.setMaximum(0)
        self.farSpinBox.setMaximum(0)
        self.lostSpinBox.setMaximum(0)
        self.maxRecallSpinBox.setMaximum(0)

    def setChart(self, chart: Optional[Chart]):
        if isinstance(chart, Chart):
            self.__chart = chart
            self.setLimits(chart)
        else:
            self.__chart = None
            self.resetLimits()
        self.updateValidateLabel()

    def validateScore(self) -> ScoreValidateResult:
        if not isinstance(self.__chart, Chart):
            return ScoreValidateResult.ChartInvalid

        score = self.value()

        if score.pure is None or score.far is None:
            return ScoreValidateResult.ScoreIncomplete

        score_range = calculate_score_range(self.__chart.notes, score.pure, score.far)
        note_in_range = score.pure + score.far + score.lost <= self.__chart.notes
        score_in_range = score_range[0] <= score.score <= score_range[1]
        if not score_in_range or not note_in_range:
            return ScoreValidateResult.ScoreMismatch
        if score.score == 0:
            return ScoreValidateResult.ScoreEmpty
        return ScoreValidateResult.Ok

    def updateValidateLabel(self):
        validate = self.validateScore()

        if validate == ScoreValidateResult.Ok:
            text = QCoreApplication.translate("ScoreEditor", "validate.ok")
        elif validate == ScoreValidateResult.ChartInvalid:
            text = QCoreApplication.translate("ScoreEditor", "validate.chartInvalid")
        elif validate == ScoreValidateResult.ScoreMismatch:
            text = QCoreApplication.translate("ScoreEditor", "validate.scoreMismatch")
        elif validate == ScoreValidateResult.ScoreEmpty:
            text = QCoreApplication.translate("ScoreEditor", "validate.scoreEmpty")
        elif validate == ScoreValidateResult.ScoreIncomplete:
            text = QCoreApplication.translate("ScoreEditor", "validate.scoreIncomplete")
        else:
            text = QCoreApplication.translate("ScoreEditor", "validate.unknownState")

        self.validateLabel.setText(text)

    def __getItemBaseName(self, item: QLineEdit | QSpinBox | QDateTimeEdit | QComboBox):
        if isinstance(item, QSpinBox):
            return item.objectName().replace("SpinBox", "")
        elif isinstance(item, QLineEdit):
            if item.objectName() == "scoreLineEdit":
                return "score"
            return item.objectName().replace("LineEdit", "")
        elif isinstance(item, QComboBox):
            return item.objectName().replace("ComboBox", "")
        elif isinstance(item, QDateTimeEdit):
            return "date"

    def __getItemNoneCheckBox(self, itemBaseName: str) -> QCheckBox | None:
        return self.findChild(QCheckBox, f"{itemBaseName}NoneCheckBox")

    def __getItemEnabled(self, itemBaseName: str):
        return not self.__getItemNoneCheckBox(itemBaseName).isChecked()

    def getItemValue(self, item: QLineEdit | QSpinBox | QDateTimeEdit | QComboBox):
        if isinstance(item, QDateTimeEdit) and item.objectName() == "dateTimeEdit":
            return (
                None
                if self.dateNoneCheckBox.isChecked()
                else self.dateTimeEdit.dateTime().toSecsSinceEpoch()
            )

        itemBaseName = self.__getItemBaseName(item)
        itemEnabled = self.__getItemEnabled(itemBaseName)

        if isinstance(item, QSpinBox):
            return item.value() if itemEnabled else None
        elif isinstance(item, QLineEdit):
            return item.text() if itemEnabled else None
        elif isinstance(item, QComboBox):
            return item.currentData() if itemEnabled else None

    def value(self):
        if not isinstance(self.__chart, Chart):
            return

        score = Score(
            song_id=self.__chart.song_id, rating_class=self.__chart.rating_class
        )
        if self.__score_id is not None:
            score.id = self.__score_id
        score.score = self.score()
        score.pure = self.getItemValue(self.pureSpinBox)
        score.far = self.getItemValue(self.farSpinBox)
        score.lost = self.getItemValue(self.lostSpinBox)
        score.date = self.getItemValue(self.dateTimeEdit)
        score.max_recall = self.getItemValue(self.maxRecallSpinBox)
        score.modifier = self.getItemValue(self.modifierComboBox)
        score.clear_type = self.getItemValue(self.clearTypeComboBox)
        score.comment = self.getItemValue(self.commentLineEdit)
        return score

    def setItemValue(
        self, item: QLineEdit | QSpinBox | QDateTimeEdit | QComboBox, value: Any
    ):
        if isinstance(item, QDateTimeEdit) and item.objectName() == "dateTimeEdit":
            if value is None:
                self.dateNoneCheckBox.setChecked(True)
            else:
                self.dateNoneCheckBox.setChecked(False)
                self.dateTimeEdit.setDateTime(QDateTime.fromSecsSinceEpoch(value))

        itemBaseName = self.__getItemBaseName(item)
        itemNoneCheckBox = self.__getItemNoneCheckBox(itemBaseName)

        if value is None:
            itemNoneCheckBox.setChecked(True)
            return
        else:
            itemNoneCheckBox.setChecked(False)

        if isinstance(item, QSpinBox):
            item.setValue(value)
        elif isinstance(item, QLineEdit):
            item.setText(value)
        elif isinstance(item, QComboBox):
            item.setCurrentIndex(value)

    def setValue(self, score: Score):
        if not isinstance(score, Score):
            return

        if score.id is not None:
            self.__score_id = score.id
            self.idLabel.setText(str(self.__score_id))
        scoreText = str(score.score)
        scoreText = scoreText.rjust(8, "0")
        self.scoreLineEdit.setText(scoreText)

        self.setItemValue(self.pureSpinBox, score.pure)
        self.setItemValue(self.farSpinBox, score.far)
        self.setItemValue(self.lostSpinBox, score.lost)
        self.setItemValue(self.dateTimeEdit, score.date)
        self.setItemValue(self.maxRecallSpinBox, score.max_recall)
        self.setItemValue(self.modifierComboBox, score.modifier)
        self.setItemValue(self.clearTypeComboBox, score.clear_type)
        self.setItemValue(self.commentLineEdit, score.comment)

    def reset(self):
        self.setChart(None)
        self.scoreLineEdit.setText("''")
        self.pureSpinBox.setValue(0)
        self.farSpinBox.setValue(0)
        self.lostSpinBox.setValue(0)
        self.maxRecallSpinBox.setValue(0)
        self.modifierComboBox.setCurrentIndex(-1)
        self.clearTypeComboBox.setCurrentIndex(-1)
        self.commentLineEdit.setText("")
