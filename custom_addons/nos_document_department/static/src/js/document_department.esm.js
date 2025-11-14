import {DocumentsDetailsPanel} from "@documents/components/documents_details_panel/documents_details_panel";
import {patch} from "@web/core/utils/patch";
import {Field} from "@web/views/fields/field";

patch(DocumentsDetailsPanel, {
    components: {...DocumentsDetailsPanel.components, Field},
});
