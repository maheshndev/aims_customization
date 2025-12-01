// frappe.ui.form.on('Item', {
//     refresh(frm) {
//         frm.trigger("toggle_fields");
//     },

//     is_mould_item(frm) {
//         frm.trigger("toggle_fields");
//     },

//     is_moulding(frm) {
//         frm.trigger("toggle_fields");
//     },

//     toggle_fields(frm) {
//         let mould_item = frm.doc.is_mould_item;
//         let moulding = frm.doc.is_moulding;

//         // Fields to show/hide and make mandatory
//         let fields = [
//             "shape", "material_type", "no_of_cavity", "side_cores", 
//             "side_cores_qty", "hot_runner_system", "cold_runner_system",
//             "tool_life", "total_shots"
//         ];

//         if (mould_item) {
//             // 1️⃣ If is_mould_item = checked
//             frm.set_df_property("mould_selection_table", "reqd", 1);

//             fields.forEach(f => {
//                 frm.set_df_property(f, "hidden", 1);
//                 frm.set_df_property(f, "reqd", 0);
//             });

//             frm.set_df_property("mould_selection_table", "hidden", 0);
//         }
//         else if (moulding) {
//             // 2️⃣ If is_moulding = checked
//             frm.set_df_property("mould_selection_table", "hidden", 1);
//             frm.set_df_property("mould_selection_table", "reqd", 0);

//             fields.forEach(f => {
//                 frm.set_df_property(f, "hidden", 0);
//                 frm.set_df_property(f, "reqd", 1);
//             });
//         }
//         else {
//             // 3️⃣ If none selected -> Reset
//             frm.set_df_property("mould_selection_table", "hidden", 0);
//             frm.set_df_property("mould_selection_table", "reqd", 0);

//             fields.forEach(f => {
//                 frm.set_df_property(f, "hidden", 0);
//                 frm.set_df_property(f, "reqd", 0);
//             });
//         }
//     }
// });


frappe.ui.form.on('Item', {

    refresh(frm) {
        frm.trigger("toggle_fields_based_on_checkboxes");
    },

    is_moulding(frm) {
        frm.trigger("toggle_fields_based_on_checkboxes");
    },

    is_mould_item(frm) {
        frm.trigger("toggle_fields_based_on_checkboxes");
    },

    toggle_fields_based_on_checkboxes(frm) {

        // Fields to hide or show
        const other_fields = [
            'shape',
            'material_type',
            'no_of_cavity',
            'side_cores',
            'side_cores_qty',
            'hot_runner_system',
            'cold_runner_system',
            'tool_life',
            'total_shots'
        ];

        if (frm.doc.is_moulding) {

            // Make mould_selection_table mandatory
            frm.set_df_property('mould_selection_table', 'reqd', 1);
            frm.set_df_property('mould_selection_table', 'hidden', 0);

            // Hide & remove mandatory from other fields
            other_fields.forEach(field => {
                frm.set_df_property(field, 'hidden', 1);
                frm.set_df_property(field, 'reqd', 0);
            });

        } else if (frm.doc.is_mould_item) {

            // Hide mould_selection_table
            frm.set_df_property('mould_selection_table', 'hidden', 1);
            frm.set_df_property('mould_selection_table', 'reqd', 0);

            // Show & make other fields mandatory
            other_fields.forEach(field => {
                frm.set_df_property(field, 'hidden', 0);
                frm.set_df_property(field, 'reqd', 1);
            });

        } else {
            // If both unchecked → reset everything (optional)
            frm.set_df_property('mould_selection_table', 'hidden', 0);
            frm.set_df_property('mould_selection_table', 'reqd', 0);

            other_fields.forEach(field => {
                frm.set_df_property(field, 'hidden', 0);
                frm.set_df_property(field, 'reqd', 0);
            });
        }

        frm.refresh_fields();
    }
});
