import datetime
import json
import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Specimen Tracker", page_icon="🧫")
st.title("🐠 Specimen Inventory Tracker")
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

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "specimens.json"


def load_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as fh:
                records = json.load(fh)
            df = pd.DataFrame(records)
            # ensure Step History column exists
            if "Step History" not in df.columns:
                df["Step History"] = df.apply(
                    lambda r: [{"step": r.get("Current Step", "Collected"), "start_date": r.get("Date Added", datetime.date.today().isoformat()), "end_date": None}],
                    axis=1,
                )
            return df
        except Exception:
            return None
    return None


def save_data(df: pd.DataFrame):
    # convert non-serializable objects to basic types
    records = df.to_dict(orient="records")
    with open(DATA_FILE, "w", encoding="utf-8") as fh:
        json.dump(records, fh, default=str, indent=2)


if "df" not in st.session_state:
    loaded = load_data()
    if loaded is not None:
        st.session_state.df = loaded
    else:
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
            # Step history: list of dicts with step, start_date, end_date
            "Step History": [
                {
                    "step": step,
                    "start_date": (datetime.date.today() - datetime.timedelta(days=16 - i * 2)).isoformat(),
                    "end_date": None,
                }
            ],
            "Comments": "",
            "Standard Length": "",
            "Total Length": "",
            "IACUC #": "",
            "Collections permit #": "",
        }
        for i, (name, step) in enumerate(
            [
                ("Sample A", "Collected"),
                ("Sample B", "Formalin"),
                # normalize sample steps to match STAGES
                ("Sample C", "Ethanol 25%-Step UP"),
                ("Sample D", "Sudan black"),
                ("Sample E", "Destain 50% Ethanol"),
                ("Sample F", "100% Glycerol"),
                ("Sample G", "Imaging"),
                ("Sample H", "Stored"),
            ]
        )
    ]
        st.session_state.df = pd.DataFrame(sample_data)
    # ensure Step History column exists for older datasets
    if "Step History" not in st.session_state.df.columns:
        st.session_state.df["Step History"] = st.session_state.df.apply(
            lambda r: [
                {"step": r["Current Step"], "start_date": r["Date Added"], "end_date": None}
            ],
            axis=1,
        )
    # ensure new metadata columns exist for older or restored sessions
    for col in ["Standard Length", "Total Length", "IACUC #", "Collections permit #"]:
        if col not in st.session_state.df.columns:
            st.session_state.df[col] = ""
    # persist initial sample data
    try:
        save_data(st.session_state.df)
    except Exception:
        pass

tab1, tab2, tab3 = st.tabs(["Inventory", "Status", "Steps to follow"])

with tab1:
    st.header("Log a new specimen")
    with st.form("add_specimen_form"):
        specimen_name = st.text_input("Specimen name")
        museum_loan = st.text_input("Museum loan #")
        source = st.text_input("Source")
        standard_length = st.text_input("Standard length")
        total_length = st.text_input("Total length")
        iacuc_number = st.text_input("IACUC #")
        collections_permit = st.text_input("Collections permit #")
        submit_specimen = st.form_submit_button("Log specimen")

    if submit_specimen:
        specimen_ids = [int(_) for _ in st.session_state.df["Specimen ID"].str.replace("SPEC-", "", regex=False)]
        next_id = max(specimen_ids) + 1 if specimen_ids else 1001
        today = datetime.date.today().isoformat()
        new_specimen = {
            "Specimen ID": f"SPEC-{next_id}",
            "Specimen Name": specimen_name or f"Specimen {next_id}",
            "Current Step": "Collected",
            "Imaged": False,
            "Museum loan #": museum_loan or f"LOAN-{next_id}",
            "Source": source,
            "Standard Length": standard_length,
            "Total Length": total_length,
            "IACUC #": iacuc_number,
            "Collections permit #": collections_permit,
            "Date Added": today,
            "Last Updated": today,
            "Comments": "",
            "Step History": [{"step": "Collected", "start_date": today, "end_date": None}],
        }
        new_row = pd.DataFrame([new_specimen])
        st.session_state.df = pd.concat([new_row, st.session_state.df], ignore_index=True)
        st.success(f"Logged {new_specimen['Specimen ID']}.")
        st.dataframe(new_row, use_container_width=True, hide_index=True)
        try:
            save_data(st.session_state.df)
        except Exception:
            st.warning("Failed to save specimen to disk. Changes are kept in this session.")

    st.header("Inventory")
    st.write(f"Total specimens: **{len(st.session_state.df)}**")
    st.info(
        "Edit the current step, imaging status, or comments directly in the table to track progress."
        " Specimens start at 'Collected' and are updated as they move through the workflow.",
        icon="🐟",
    )

    specimen_options = (
        st.session_state.df["Specimen ID"] + " | " + st.session_state.df["Specimen Name"]
    ).tolist()
    delete_selection = st.multiselect(
        "Select specimens to delete",
        options=specimen_options,
        help="Choose specimen rows to remove from the inventory.",
    )
    if st.button("Delete selected specimens", type="danger"):
        if delete_selection:
            delete_ids = [item.split(" | ")[0] for item in delete_selection]
            before_count = len(st.session_state.df)
            st.session_state.df = st.session_state.df[~st.session_state.df["Specimen ID"].isin(delete_ids)].reset_index(drop=True)
            deleted_count = before_count - len(st.session_state.df)
            st.success(f"Deleted {deleted_count} specimen row(s).")
        else:
            st.warning("Select at least one specimen to delete.")

    edited_df = st.data_editor(
        st.session_state.df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Current Step": st.column_config.SelectboxColumn(
                "Current step",
                options=STAGES,
            ),
            "Imaged": st.column_config.CheckboxColumn("Imaged"),
            "Comments": st.column_config.TextColumn("Comments"),
            "Standard Length": st.column_config.TextColumn("Standard length"),
            "Total Length": st.column_config.TextColumn("Total length"),
            "IACUC #": st.column_config.TextColumn("IACUC #"),
            "Collections permit #": st.column_config.TextColumn("Collections permit #"),
        },
        disabled=["Specimen ID", "Date Added", "Last Updated"],
    )

    if not edited_df.equals(st.session_state.df):
        # update "Last Updated" only for rows that changed
        prev = st.session_state.df.copy()
        # align indexes and fill NaN for comparison
        diff_mask = (edited_df.fillna("") != prev.fillna("")) .any(axis=1)
        today_iso = datetime.date.today().isoformat()
        # handle step changes and append to Step History
        for idx in edited_df.index[diff_mask]:
            prev_step = prev.at[idx, "Current Step"]
            new_step = edited_df.at[idx, "Current Step"]
            if prev_step != new_step:
                # copy history from previous and update
                history = prev.at[idx, "Step History"] if "Step History" in prev.columns else []
                # ensure we have a list copy
                history = list(history) if history is not None else []
                # close previous history entry
                if history:
                    history[-1] = dict(history[-1])
                    if history[-1].get("end_date") is None:
                        history[-1]["end_date"] = today_iso
                else:
                    # if no history, create one for prev step
                    history.append({"step": prev_step, "start_date": prev.at[idx, "Date Added"], "end_date": today_iso})
                # append new entry for the new step
                history.append({"step": new_step, "start_date": today_iso, "end_date": None})
                edited_df.at[idx, "Step History"] = history
        edited_df.loc[diff_mask, "Last Updated"] = today_iso
        st.session_state.df = edited_df
        try:
            save_data(st.session_state.df)
        except Exception:
            st.warning("Failed to save edits to disk. Changes are kept in this session.")

    st.header("Workflow metrics")
    col1, col2, col3 = st.columns(3)
    num_imaged = int(st.session_state.df[st.session_state.df.Imaged].shape[0])
    num_pending = int(st.session_state.df[~st.session_state.df.Imaged].shape[0])
    col1.metric(label="Total specimens", value=len(st.session_state.df))
    col2.metric(label="Imaged specimens", value=num_imaged)
    col3.metric(label="Pending imaging", value=num_pending)

    # calculate average total days spent at each stage across specimens using Step History
    today = datetime.date.today()
    # prepare per-specimen totals per step
    per_step_lists = {step: [] for step in STAGES}
    for _, row in st.session_state.df.iterrows():
        # initialize per-specimen dict
        spec_totals = {step: 0 for step in STAGES}
        history = row.get("Step History") or []
        for entry in history:
            try:
                start = datetime.date.fromisoformat(entry["start_date"])
            except Exception:
                continue
            end = None
            if entry.get("end_date"):
                try:
                    end = datetime.date.fromisoformat(entry["end_date"])
                except Exception:
                    end = today
            else:
                end = today
            days = (end - start).days
            if entry.get("step") in spec_totals:
                spec_totals[entry.get("step")] += days
        # append to lists (0 if not visited)
        for step in STAGES:
            per_step_lists[step].append(spec_totals.get(step, 0))
    # compute average across specimens
    stage_counts = (
        pd.DataFrame({"Current Step": list(per_step_lists.keys()), "Avg Days": [
            (sum(vals) / len(vals)) if vals else 0 for vals in per_step_lists.values()
        ]})
        .set_index("Current Step")
        .reindex(STAGES, fill_value=0)
        .reset_index()
    )
    # ensure numeric type and a non-zero domain for plotting
    stage_counts["Avg Days"] = stage_counts["Avg Days"].astype(float)
    stage_x_max = max(stage_counts["Avg Days"].max(), 1.0) * 1.05

    st.subheader("Specimen stage distribution")
    stage_plot = (
        alt.Chart(stage_counts)
        .mark_bar()
        .encode(
            x=alt.X("Avg Days:Q", title="Average days at step", scale=alt.Scale(domain=[0, stage_x_max])),
            y=alt.Y("Current Step:N", sort=STAGES, title="Workflow step"),
            color=alt.Color("Current Step:N", legend=None),
            tooltip=["Current Step", "Avg Days"],
        )
        .properties(height=320)
    )
    st.altair_chart(stage_plot, use_container_width=True)

    st.subheader("Specimen status")
    specimen_options = (
        st.session_state.df["Specimen ID"] + " | " + st.session_state.df["Specimen Name"]
    ).tolist()
    selected_specimen = st.selectbox("Choose specimen to inspect", specimen_options)
    selected_id = selected_specimen.split(" | ")[0]
    selected_row = st.session_state.df.loc[st.session_state.df["Specimen ID"] == selected_id].iloc[0]

    status_col1, status_col2, status_col3 = st.columns(3)
    status_col1.metric("Current step", selected_row["Current Step"])
    status_col2.metric("Imaged", "Yes" if selected_row["Imaged"] else "No")
    status_col3.metric("Last updated", selected_row["Last Updated"])

    selected_stage_index = STAGES.index(selected_row["Current Step"]) if selected_row["Current Step"] in STAGES else 0
    # compute days spent per workflow step for the selected specimen from Step History
    sel_history = selected_row.get("Step History") or []
    sel_totals = {step: 0 for step in STAGES}
    for entry in sel_history:
        try:
            start = datetime.date.fromisoformat(entry.get("start_date"))
        except Exception:
            continue
        if entry.get("end_date"):
            try:
                end = datetime.date.fromisoformat(entry.get("end_date"))
            except Exception:
                end = today
        else:
            end = today
        days = (end - start).days
        if entry.get("step") in sel_totals:
            sel_totals[entry.get("step")] += days

    specimen_progress = pd.DataFrame(
        {
            "Workflow step": STAGES,
            "Days at Step": [sel_totals.get(step, 0) for step in STAGES],
            "Selected": [1 if idx == selected_stage_index else 0 for idx, _ in enumerate(STAGES)],
        }
    )
    # align x-axis domain with the average-days stage plot for consistent comparison
    max_avg_days = float(stage_counts["Avg Days"].max()) if not stage_counts.empty else 0.0
    max_sel_days = max(specimen_progress["Days at Step"]) if not specimen_progress.empty else 0.0
    x_max = max(max_avg_days, max_sel_days, 1.0) * 1.05
    specimen_chart = (
        alt.Chart(specimen_progress)
        .mark_bar()
        .encode(
            x=alt.X("Days at Step:Q", title="Days at step", scale=alt.Scale(domain=[0, x_max])),
            y=alt.Y("Workflow step:N", sort=STAGES, title="Workflow step"),
            color=alt.condition(
                alt.datum["Selected"] == 1,
                alt.value("#2ca02c"),
                alt.value("#d3d3d3"),
            ),
            tooltip=["Workflow step", "Days at Step"],
        )
        .properties(height=380)
    )
    st.altair_chart(specimen_chart, use_container_width=True)

    # Timeline (Gantt-like) view for the selected specimen's step history
    sel_history = selected_row.get("Step History") or []
    timeline_rows = []
    for entry in sel_history:
        try:
            start = datetime.date.fromisoformat(entry.get("start_date"))
        except Exception:
            continue
        if entry.get("end_date"):
            try:
                end = datetime.date.fromisoformat(entry.get("end_date"))
            except Exception:
                end = today
        else:
            end = today
        timeline_rows.append({"step": entry.get("step"), "start": pd.to_datetime(start), "end": pd.to_datetime(end)})

    if timeline_rows:
        timeline_df = pd.DataFrame(timeline_rows).dropna()
        timeline_chart = (
            alt.Chart(timeline_df)
            .mark_bar()
            .encode(
                x=alt.X("start:T", title="Start"),
                x2=alt.X2("end:T"),
                y=alt.Y("step:N", sort=STAGES, title="Workflow step"),
                color=alt.Color("step:N", legend=None),
                tooltip=[alt.Tooltip("step", title="Step"), alt.Tooltip("start", title="Start"), alt.Tooltip("end", title="End")],
            )
            .properties(height=200)
        )
        st.subheader("Selected specimen timeline")
        st.altair_chart(timeline_chart, use_container_width=True)
    else:
        st.info("No step history available for this specimen.")

    st.subheader("Imaging status")
    imaged_counts = (
        st.session_state.df["Imaged"].value_counts().reindex([False, True], fill_value=0).reset_index()
    )
    imaged_counts.columns = ["Imaged", "Count"]
    imaged_pie = (
        alt.Chart(imaged_counts)
        .mark_arc(innerRadius=50)
        .encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Imaged", type="nominal", scale=alt.Scale(domain=[False, True], range=["#d62728", "#2ca02c"]), title="Imaged"),
            tooltip=[alt.Tooltip("Count", title="Specimen count"), alt.Tooltip("Imaged", title="Imaged")],
        )
        .properties(height=300)
    )
    st.altair_chart(imaged_pie, use_container_width=True)

with tab2:
    st.header("Update specimen status")
    st.write("Use this tab to change a specimen\'s current workflow step and update the inventory current-step chart.")

    current_counts = (
        st.session_state.df["Current Step"].value_counts()
        .reindex(STAGES, fill_value=0)
        .reset_index()
    )
    current_counts.columns = ["Current Step", "Count"]
    status_chart = (
        alt.Chart(current_counts)
        .mark_bar()
        .encode(
            x=alt.X("Count:Q", title="Specimen count", scale=alt.Scale(domain=[0, max(current_counts["Count"].max(), 1)])),
            y=alt.Y("Current Step:N", sort=STAGES, title="Current step"),
            color=alt.Color("Current Step:N", legend=None),
            tooltip=["Current Step", "Count"],
        )
        .properties(height=360)
    )
    st.altair_chart(status_chart, use_container_width=True)

    specimen_options = (
        st.session_state.df["Specimen ID"] + " | " + st.session_state.df["Specimen Name"]
    ).tolist()
    selected_specimen = st.selectbox("Choose specimen", specimen_options)
    selected_id = selected_specimen.split(" | ")[0]
    selected_row = st.session_state.df.loc[st.session_state.df["Specimen ID"] == selected_id].iloc[0]

    with st.form("update_status_form"):
        st.markdown(f"**Current step:** {selected_row['Current Step']}")
        new_step = st.selectbox(
            "New current step",
            STAGES,
            index=STAGES.index(selected_row["Current Step"]) if selected_row["Current Step"] in STAGES else 0,
        )
        update_step = st.form_submit_button("Update step")

    if update_step:
        if new_step != selected_row["Current Step"]:
            idx = st.session_state.df.index[st.session_state.df["Specimen ID"] == selected_id][0]
            today_iso = datetime.date.today().isoformat()
            st.session_state.df.at[idx, "Current Step"] = new_step
            st.session_state.df.at[idx, "Last Updated"] = today_iso
            history = selected_row.get("Step History") or []
            history = list(history)
            if history:
                history[-1] = dict(history[-1])
                if history[-1].get("end_date") is None:
                    history[-1]["end_date"] = today_iso
            else:
                history.append({"step": selected_row["Current Step"], "start_date": selected_row["Date Added"], "end_date": today_iso})
            history.append({"step": new_step, "start_date": today_iso, "end_date": None})
            st.session_state.df.at[idx, "Step History"] = history
            st.success(f"Updated {selected_id} to {new_step}.")
            try:
                save_data(st.session_state.df)
            except Exception:
                st.warning("Failed to persist update; change is in-memory only.")
        else:
            st.info("The specimen is already at that step.")

with tab3:
    st.header("Steps to follow")
    st.write(
        "Use this tab as a workflow guide to move specimens through each staining and imaging stage."
    )
    step_guide = [
        {"Step": step, "Action": action}
        for step, action in [
            ("Collected", "Record specimen details and start initial processing."),
            ("Formalin", "Fix the specimen in 10% buffered formalin to preserve tissue."),
            ("Formalin rinse", "Rinse the specimen to remove excess formalin."),
            ("Trypsin", "Digest proteins gently with trypsin. This step must be monitored closely."),
            ("Ethanol 25%-Step UP", "Begin ethanol dehydration at 25% concentration."),
            ("Ethanol 50%-Step UP", "Continue dehydration with 50% ethanol."),
            ("Ethanol 75%-Step UP", "Advance dehydration with 75% ethanol."),
            ("Sudan black", "Stain the specimen with Sudan black B. Monitor progression using the scope."),
            ("Destain 50% Ethanol", "Begin destaining in 50% ethanol."),
            ("Destain 25% Ethanol", "Continue destaining in 25% ethanol."),
            ("DI Water", "Rinse the specimen with deionized water."),
            ("70:30 Water:Glycerol", "Move the specimen into a 70:30 water:glycerol solution."),
            ("50:50 Water:Glycerol", "Equilibrate in an equal mixture of water and glycerol."),
            ("25:75 Water:Glycerol", "Transition into a 25:75 water:glycerol mixture."),
            ("100% Glycerol", "Place the specimen in pure glycerol."),
            ("Imaging", "Capture imaging data once the specimen is ready."),
            ("Stored", "Store the specimen in the final storage medium."),
        ]
    ]
    st.table(pd.DataFrame(step_guide))
