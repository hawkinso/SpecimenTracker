import datetime

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Specimen Tracker", page_icon="🧫")
st.title("🧪 Specimen Inventory Tracker")
st.write(
    """
    Track specimens through staining, imaging, and storage workflows.
    Add specimens, update their current stain step, and monitor imaging status.
    """
)

STAGES = [
    "Collected",
    "Formalin",
    "Formalin rinse",
    "Trypsin",
    "Ethanol 25%-Step UP",
    "Ethanol 50%-Step UP",
    "Ethanol 75%-Step UP",
    "Sudan black",
    "Destain 50% Ethanol",
    "Destain 25% Ethanol",
    "DI Water",
    "70:30 Water:Glycerol",
    "50:50 Water:Glycerol",
    "25:75 Water:Glycerol",
    "100% Glycerol",
    "Imaging",
    "Stored",
]

if "df" not in st.session_state:
    sample_data = [
        {
            "Specimen ID": f"SPEC-{1000 + i}",
            "Specimen Name": name,
            "Museum loan #": f"LOAN-{1000 + i}",
            "Source": f"Source-{1000 + i}",
            "Current Step": step,
            "Imaged": i % 3 == 0,
            "Date Added": (datetime.date.today() - datetime.timedelta(days=16 - i * 2)).isoformat(),
            "Last Updated": (datetime.date.today() - datetime.timedelta(days=16 - i * 2)).isoformat(),
            "Comments": "",
        }
        for i, (name, step) in enumerate(
            [
                ("Sample A", "Collected"),
                ("Sample B", "Formalin"),
                ("Sample C", "Ethanol step up"),
                ("Sample D", "Sudan black"),
                ("Sample E", "Destain"),
                ("Sample F", "Glycerol"),
                ("Sample G", "Imaging"),
                ("Sample H", "Stored"),
            ]
        )
    ]
    st.session_state.df = pd.DataFrame(sample_data)

st.header("Add a specimen")
with st.form("add_specimen_form"):
    specimen_name = st.text_input("Specimen name")
    current_step = st.selectbox("Current step", STAGES)
    imaged = st.checkbox("Imaged")
    comments = st.text_area("Comments")
    submit_specimen = st.form_submit_button("Add specimen")

if submit_specimen:
    specimen_ids = [int(_) for _ in st.session_state.df["Specimen ID"].str.replace("SPEC-", "")]
    next_id = max(specimen_ids) + 1 if specimen_ids else 1001
    today = datetime.date.today().isoformat()
    new_specimen = {
        "Specimen ID": f"SPEC-{next_id}",
        "Specimen Name": specimen_name or f"Specimen {next_id}",
        "Current Step": current_step,
        "Imaged": imaged,
        "Date Added": today,
        "Last Updated": today,
        "Comments": comments,
    }
    new_row = pd.DataFrame([new_specimen])
    st.session_state.df = pd.concat([new_row, st.session_state.df], ignore_index=True)
    st.success(f"Added {new_specimen['Specimen ID']}.")
    st.dataframe(new_row, use_container_width=True, hide_index=True)

st.header("Inventory")
st.write(f"Total specimens: **{len(st.session_state.df)}**")
st.info(
    "Edit the current step, imaging status, or comments directly in the table."
    " Use the stage chart below to monitor workflow progress.",
    icon="🧬",
)

edited_df = st.data_editor(
    st.session_state.df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Current Step": st.column_config.SelectboxColumn(
            "Current step",
            options=STAGES,
        ),
        "Imaged": st.column_config.BooleanColumn("Imaged"),
        "Comments": st.column_config.TextAreaColumn("Comments"),
    },
    disabled=["Specimen ID", "Date Added", "Last Updated"],
)

if not edited_df.equals(st.session_state.df):
    st.session_state.df = edited_df

st.header("Workflow metrics")
col1, col2, col3 = st.columns(3)
num_imaged = int(st.session_state.df[st.session_state.df.Imaged].shape[0])
num_pending = int(st.session_state.df[~st.session_state.df.Imaged].shape[0])
col1.metric(label="Total specimens", value=len(st.session_state.df))
col2.metric(label="Imaged specimens", value=num_imaged)
col3.metric(label="Pending imaging", value=num_pending)

stage_counts = (
    st.session_state.df.groupby("Current Step").size().reset_index(name="Count")
)

st.subheader("Specimen stage distribution")
stage_plot = (
    alt.Chart(stage_counts)
    .mark_bar()
    .encode(
        x=alt.X("Count:Q", title="Specimen count"),
        y=alt.Y("Current Step:N", sort=STAGES, title="Workflow step"),
        color=alt.Color("Current Step:N", legend=None),
        tooltip=["Current Step", "Count"],
    )
    .properties(height=320)
)
st.altair_chart(stage_plot, use_container_width=True)

st.subheader("Imaging status")
imaged_pie = (
    alt.Chart(st.session_state.df)
    .mark_arc(innerRadius=50)
    .encode(
        theta=alt.Theta(field="Imaged", type="quantitative", aggregate="count"),
        color=alt.Color(field="Imaged", type="nominal", scale=alt.Scale(domain=[False, True], range=["#d62728", "#2ca02c"]), title="Imaged"),
        tooltip=[alt.Tooltip("count()", title="Specimen count")],
    )
    .properties(height=300)
)
st.altair_chart(imaged_pie, use_container_width=True)
