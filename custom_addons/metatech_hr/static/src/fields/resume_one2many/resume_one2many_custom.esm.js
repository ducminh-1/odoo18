/** @odoo-module */

import {
    SkillsX2ManyField,
    skillsX2ManyField,
} from "@hr_skills/fields/skills_one2many/skills_one2many";
import {onWillStart, useRef, useState} from "@odoo/owl";
import {CommonSkillsListRenderer} from "@hr_skills/views/skills_list_renderer";
import {_t} from "@web/core/l10n/translation";
import {formatDate} from "@web/core/l10n/dates";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

const DEFAULT_RESUME_TYPE = [
    "resume_type_working_process",
    "resume_type_learning_process",
    "resume_type_reward",
    "resume_type_discipline",
    "resume_type_pros_and_cons",
];
const COLUMN_MAP = {
    resume_type_working_process: ["sequence", "date_start", "description"],
    resume_type_learning_process: [
        "sequence",
        "date_start",
        "course_name",
        "description",
    ],
    resume_type_reward: ["sequence", "date_start", "description"],
    resume_type_discipline: ["sequence", "date_start", "description"],
    resume_type_pros_and_cons: ["sequence", "type_of_pros_and_cons", "description"],
};

const COLUMN_LABEL_MAP = {
    resume_type_working_process: _t("Description"),
    resume_type_learning_process: _t("Result"),
    resume_type_reward: _t("Reward Content"),
    resume_type_discipline: _t("Type of violation"),
    resume_type_pros_and_cons: _t("Content"),
};

const COLUMN_NORMAL = ["sequence", "date_start", "date_end", "name", "description"];

export class ResumeListRenderer extends CommonSkillsListRenderer {
    static useMagicColumnWidths = false;
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.resumeTypelist = useState([]);
        this.resumeTypelistWithXMLId = useState([]);
        this.tableRef = useRef("root");

        onWillStart(async () => {
            try {
                const [resumeTypes] = await Promise.all([
                    this.orm.searchRead(
                        "hr.resume.line.type",
                        [],
                        ["id", "name", "sequence"],
                        {}
                    ),
                    // This.orm.searchRead(
                    //     "ir.model.data",
                    //     [
                    //         ["model", "=", "hr.resume.line.type"],
                    //         ["res_id", "=", []],
                    //     ],
                    //     ["name", "res_id"]
                    // ),
                ]);

                this.resumeTypelist = resumeTypes;

                const resIds = resumeTypes.map((r) => r.id);
                this.resumeTypelistWithXMLId = await this.orm.searchRead(
                    "ir.model.data",
                    [
                        ["model", "=", "hr.resume.line.type"],
                        ["res_id", "in", resIds],
                    ],
                    ["name", "res_id"]
                );
            } catch (error) {
                console.error("Error fetching data:", error);
            }
        });
    }

    get groupBy() {
        return "line_type_id";
    }

    get colspan() {
        if (this.props.activeActions) {
            return 3;
        }
        return 2;
    }

    formatDate(date) {
        return formatDate(date);
    }

    get groupedListResume() {
        const grouped = {};
        const lineTypes = this.resumeTypelist.sort((a, b) => a.sequence - b.sequence);
        for (const type of lineTypes) {
            const xmlId = this.resumeTypelistWithXMLId.find(
                (t) => t.res_id === type.id
            );
            grouped[type.name] = {
                id: type.id,
                name: type.name,
                sequence: type.sequence,
                list: {
                    records: [],
                    xmlId:
                        xmlId && DEFAULT_RESUME_TYPE.includes(xmlId.name)
                            ? xmlId.name
                            : null,
                },
            };
        }
        const resumeLines = this.props.list.records;
        for (const line of resumeLines) {
            const typeId = line.data.line_type_id[0];
            const typeRecord = lineTypes.find((type) => type.id === typeId);

            if (typeRecord) {
                const groupName = typeRecord.name;
                grouped[groupName].list.records.push(line);
            } else {
                const otherGroupName = _t("Other");
                if (!grouped[otherGroupName]) {
                    grouped[otherGroupName] = {
                        id: null,
                        name: otherGroupName,
                        list: {
                            records: [],
                        },
                    };
                }
                grouped[otherGroupName].list.records.push(line);
            }
        }
        return grouped;
    }

    getColumns(record) {
        const xmlId = this.resumeTypelistWithXMLId.find(
            (type) => type.res_id === record.data.line_type_id[0]
        );
        const updatedRecord = {
            ...record,
            xmlId: xmlId ? xmlId.name : null,
        };
        return this.getActiveColumnsResume(updatedRecord);
    }

    getActiveColumnsResume(list) {
        const columns = this.allColumns.filter((col) => {
            if (list.isGrouped && col.widget === "handle") {
                return false;
            }
            if (col.optional && !this.optionalActiveFields[col.name]) {
                return false;
            }
            if (this.evalColumnInvisible(col.column_invisible)) {
                return false;
            }
            if (list.xmlId && DEFAULT_RESUME_TYPE.includes(list.xmlId)) {
                const mappedColumns = COLUMN_MAP[list.xmlId];
                if (mappedColumns.includes(col.name)) {
                    if (col.name === "description") {
                        col.label = COLUMN_LABEL_MAP[list.xmlId];
                    }
                    if (col.name === "date_start") {
                        col.label = _t("Time");
                    }
                    return true;
                }
                return false;
            }
            if (COLUMN_NORMAL.includes(col.name)) {
                if (col.name === "description") {
                    col.label = _t("Description");
                }
                if (col.name === "date_start") {
                    col.label = _t("Date Start");
                }
                return true;
            }
            return false;
        });
        return columns;
    }

    freezeColumnWidths() {
        return;
    }
}
ResumeListRenderer.template = "metatech_hr.ResumeListRenderer";
ResumeListRenderer.recordRowTemplate = "web.ListRenderer.RecordRow";

export class ResumeX2ManyField extends SkillsX2ManyField {
    getWizardTitleName() {
        return _t("Create a resume line");
    }
}
ResumeX2ManyField.components = {
    ...SkillsX2ManyField.components,
    ListRenderer: ResumeListRenderer,
};

export const resumeX2ManyField = {
    ...skillsX2ManyField,
    component: ResumeX2ManyField,
};

registry.category("fields").add("resume_one2many_custom", resumeX2ManyField);
