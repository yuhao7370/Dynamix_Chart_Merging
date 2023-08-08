from math import ceil
import numpy as np
from .dynamix2dynamite import convert_json

class Note:
    SIDE_LEFT = -1
    SIDE_FRONT = 0
    SIDE_RIGHT = 1

    NOTE_NORMAL = 0
    NOTE_CHAIN = 1
    NOTE_HOLD = 2

    COLOR_NORMAL = (0, 255, 255, 255)
    COLOR_CHAIN = (255, 51, 51, 255)
    COLOR_HOLD_BOARD = (255, 255, 128, 255)
    COLOR_HOLD_FILL = (70, 134, 0, 255)

    WIDTH_NORMAL = 40
    WIDTH_CHAIN = 20
    WIDTH_HOLD = 40
    WIDTH_MIN = 20

    def __lt__(self, other):
        res = self.start - other.start
        if res != 0: return res < 0
        res = self.type - other.type
        if res != 0: return res < 0
        if self.type == self.NOTE_HOLD:
            res = self.end - other.end
            if res != 0: return res < 0
        res = self.pos - other.pos
        if res != 0: return res < 0
        res = self.width - other.width
        if res != 0: return res < 0
        return False

    def __init__(self, pos, width=1.0, side=SIDE_FRONT, type=NOTE_NORMAL, start=0.0, end=None):
        self.type = type
        self.side = side
        self.width = width
        self.pos = pos + width / 2
        self.start = start
        if end is None:
            self.end = start
        else:
            self.end = max(start, end)

    def clone(self):
        note = Note(0, 0, self.side, self.type, self.start, self.end)
        note.pos = self.pos
        note.width = self.width
        return note


class Chart:
    @classmethod
    def concatenate(cls, former_chart, latter_chart, song_length_sec):
        return former_chart.clone().concat(latter_chart, song_length_sec)

    def __init__(self):
        self.name = None
        self.map_id = None
        self.notes = []
        self.time = 0.0
        self.left_slide = False
        self.right_slide = False
        self.bar_per_min = 0.0
        self.time_offset = 0.0

    def clone(self):
        new_chart = Chart()
        new_chart.name = self.name
        new_chart.map_id = self.map_id
        new_chart.time = self.time
        new_chart.left_slide = self.left_slide
        new_chart.right_slide = self.right_slide
        new_chart.time_offset = self.time_offset
        new_chart.bar_per_min = self.bar_per_min
        for note in self.notes:
            new_chart.notes.append(note.clone())
        return new_chart

    def move(self, bar_offset):
        for note in self.notes:
            note.start = note.start + bar_offset
            note.end = note.end + bar_offset
        self.time = self.time + bar_offset
        return self

    def clip(self, start, end):
        res = self.clone()
        res.time = end - start
        new_notes = []
        for note in res.notes:
            if note.type == Note.NOTE_HOLD:
                if start <= note.start:
                    if end >= note.end:
                        new_notes.append(note)
                    elif end == note.start:
                        note.type = Note.NOTE_NORMAL
                        note.end = end
                        new_notes.append(note)
                    elif end > note.start:
                        note.end = end
                        new_notes.append(note)
                else:
                    if start == note.end:
                        note.type = Note.NOTE_CHAIN
                        note.start = start
                        new_notes.append(note)
                    elif start < note.end:
                        note.start = start
                        note.end = min(end, note.end)
                        new_notes.append(note)
            else:
                if start <= note.start and note.start <= end:
                    new_notes.append(note)
        for note in new_notes:
            note.start -= start
            note.end -= start
        res.notes = new_notes
        return res

    def concat(self, other, song_length_sec):
        other = other.change_bpm(self.bar_per_min)
        time_offset = song_length_sec + self.time_offset - other.time_offset
        bar_offset = self.bar_per_min * time_offset / 60
        for note in other.notes:
            note.start += bar_offset
            note.end += bar_offset
            self.time = max(self.time, note.end)
        self.notes.extend(other.notes)
        self.left_slide = self.left_slide and other.left_slide
        self.right_slide = self.right_slide and other.right_slide
        return self

    def change_bpm(self, new_bpm):
        new_chart = self.clone()
        new_chart.bar_per_min = new_bpm
        for note in new_chart.notes:
            note.start = new_bpm * note.start / self.bar_per_min
            note.end = new_bpm * note.end / self.bar_per_min
        return new_chart

    def change_speed(self, speed=1.0):
        new_chart = self.clone()
        new_chart.bar_per_min = self.bar_per_min * speed
        new_chart.time_offset = self.time_offset / speed
        return new_chart

    def to_dict(self):
        m_notes = []
        m_notesLeft = []
        m_notesRight = []
        data = {
            'm_Name': self.name,
            'm_mapID': self.map_id,
            'm_barPerMin': self.bar_per_min,
            'm_timeOffset': self.time_offset,
            'm_leftRegion': 1 if self.left_slide else 2,
            'm_rightRegion': 1 if self.right_slide else 2,
            'm_notes': {
                'm_notes': m_notes,
            },
            'm_notesLeft': {
                'm_notes': m_notesLeft,
            },
            'm_notesRight': {
                'm_notes': m_notesRight,
            },
        }
        note_id = 0
        for note in self.notes:
            if note.type == Note.NOTE_CHAIN:
                typ = 1
            elif note.type == Note.NOTE_HOLD:
                typ = 2
            elif note.type == Note.NOTE_NORMAL:
                typ = 0
            else:
                typ = 0
            pos = note.pos - note.width / 2
            note_dict = {
                'm_id': note_id,
                'm_type': typ,
                'm_time': note.start,
                'm_position': pos,
                'm_width': note.width,
                'm_subId': note_id + 1 if typ == 2 else -1,
            }
            note_id += 1
            if note.side == Note.SIDE_FRONT:
                m_notes.append(note_dict)
            elif note.side == Note.SIDE_LEFT:
                m_notesLeft.append(note_dict)
            elif note.side == Note.SIDE_RIGHT:
                m_notesRight.append(note_dict)
            else:
                m_notes.append(note_dict)
            if typ == 2:
                note_dict = {
                    'm_id': note_id,
                    'm_type': 3,
                    'm_time': note.end,
                    'm_position': pos,
                    'm_width': note.width,
                    'm_subId': -1,
                }
                note_id += 1
                if note.side == Note.SIDE_FRONT:
                    m_notes.append(note_dict)
                elif note.side == Note.SIDE_LEFT:
                    m_notesLeft.append(note_dict)
                elif note.side == Note.SIDE_RIGHT:
                    m_notesRight.append(note_dict)
                else:
                    m_notes.append(note_dict)
        return data

    def to_xml(self):
        return convert_json(self.to_dict())[0]

