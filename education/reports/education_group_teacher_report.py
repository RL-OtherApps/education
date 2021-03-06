# Copyright 2019 Oihane Crucelaegui - AvanzOSC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import tools
from odoo import api, fields, models
from psycopg2.extensions import AsIs


class EducationGroupTeacherReport(models.Model):
    _name = 'education.group.teacher.report'
    _description = 'Teacher Groups Report'
    _auto = False
    _rec_name = 'teacher_id'

    center_id = fields.Many2one(
        comodel_name='res.partner', string='Education Center')
    course_id = fields.Many2one(
        comodel_name='education.course', string='Education Course')
    group_id = fields.Many2one(
        comodel_name='education.group', string='Education Group')
    subject_id = fields.Many2one(
        comodel_name='education.subject', string='Education Subject')
    teacher_id = fields.Many2one(
        comodel_name='hr.employee', string='Teacher')
    classroom_id = fields.Many2one(
        comodel_name='education.classroom', string='Classroom')
    academic_year_id = fields.Many2one(
        comodel_name='education.academic_year', string='Academic Year')
    language_id = fields.Many2one(
        comodel_name='education.language', string='Language')
    subject_name = fields.Char(string="Subject Name")

    _depends = {
        'education.schedule': [
            'subject_id', 'classroom_id', 'teacher_id', 'academic_year_id'
        ],
        'education.group': [
            'center_id', 'course_id'
        ],
    }

    def _coalesce(self):
        coalesce_str = """
            , COALESCE(sub_center.name, sbt.description, tt.description,
                       'undefined') AS subject_name
        """
        return coalesce_str

    def _select(self):
        select_str = """
            SELECT
                row_number() OVER () as id,
                grp.center_id AS center_id,
                grp.course_id AS course_id,
                grp.id AS group_id,
                sch.subject_id AS subject_id,
                sch.classroom_id AS classroom_id,
                sch.teacher_id AS teacher_id,
                sch.academic_year_id AS academic_year_id,
                sch.language_id AS language_id
        """
        return select_str

    def _from(self):
        from_str = """
                FROM edu_schedule_group sch_group
                JOIN education_schedule sch ON sch_group.schedule_id = sch.id
                LEFT JOIN education_subject sbt ON sch.subject_id = sbt.id
                LEFT JOIN education_task_type tt ON sch.task_type_id = tt.id
                JOIN education_group grp ON sch_group.group_id = grp.id
                LEFT JOIN education_subject_center sub_center
                  ON sub_center.subject_id = sch.subject_id
                  AND sub_center.center_id = grp.center_id
                  AND sub_center.course_id = grp.course_id
                  AND sub_center.lang_id = sch.language_id
        """
        return from_str

    def _group_by(self):
        group_by_str = """
                GROUP BY grp.center_id, grp.course_id, grp.id, sch.subject_id,
                sch.classroom_id, sch.teacher_id, sch.academic_year_id,
                sch.language_id, sbt.description, tt.description,
                sub_center.name
        """
        return group_by_str

    @api.model_cr
    def init(self):
        # self._table = education_group_teacher_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """CREATE or REPLACE VIEW %s as
                (
                %s %s %s %s
            )""", (
                AsIs(self._table), AsIs(self._select()),
                AsIs(self._coalesce()), AsIs(self._from()),
                AsIs(self._group_by()),))
