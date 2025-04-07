# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import base64
import os
from enum import IntEnum

import jsonlines
import pandas as pd
import streamlit as st
from streamlit import session_state as state


IMAGE_DIR: str = "images"
LOGO_PATH: str = os.path.join(IMAGE_DIR, "logo/PIKE-RAG_vertical_black-font.png")
ICON_PATH: str = os.path.join(IMAGE_DIR, "logo/PIKE-RAG_icon.svg")
LOGGING_PATH: str = "loggings.jsonl"


class DecomposeStep(IntEnum):
    Initialization = 0
    Propose_Atomic_Questions = 2
    Retrieve_Relevant_Atomic_Pairs = 3
    Select_Most_Useful_Atomic_Question = 5
    Update_Context = 6
    Generate_Final_Answer = 7


def step2str(step: DecomposeStep):
    if step == DecomposeStep.Initialization:
        return "🆕Initialization"
    elif step == DecomposeStep.Propose_Atomic_Questions:
        return "💡Atomic Proposal"
    elif step == DecomposeStep.Retrieve_Relevant_Atomic_Pairs:
        return "🔎Atomic Retrieval"
    elif step == DecomposeStep.Select_Most_Useful_Atomic_Question:
        return "⚖️Atomic Selection"
    elif step == DecomposeStep.Update_Context:
        return "➕Context Updated"
    elif step == DecomposeStep.Generate_Final_Answer:
        return "🔚Answer Achieved"


table_of_content = """
### [📊Approach Overview](#_overview)
### [⚙️QA Selection](#_qa)
### [🧠Decomposition Demonstration](#_workflow)
"""


class OverviewImage(IntEnum):
    DynamicPipeline = 1
    DynamicDataCollection = 3
    DynamicDecomposerTrain = 5
    FollowDecomposeStep = 6


def get_overview_image_path():
    if state.overview_image == OverviewImage.DynamicPipeline:
        image_path = "demo/decompose_pipeline.gif"
    elif state.overview_image == OverviewImage.DynamicDataCollection:
        image_path = "demo/data_collection.gif"
    elif state.overview_image == OverviewImage.DynamicDecomposerTrain:
        image_path = "demo/decomposer_training.gif"
    else:
        if state.cur_step == DecomposeStep.Propose_Atomic_Questions:
            if state.round_idx == 0:
                image_path = "demo/2-1_proposal.png"
            else:
                image_path = "demo/2-2_proposal.png"
        elif state.cur_step == DecomposeStep.Retrieve_Relevant_Atomic_Pairs:
            image_path = "demo/3_retrieval.png"
        elif state.cur_step == DecomposeStep.Select_Most_Useful_Atomic_Question:
            image_path = "demo/4_selection.png"
        elif state.cur_step == DecomposeStep.Update_Context:
            image_path = "demo/5_update_context.png"
        elif state.cur_step == DecomposeStep.Generate_Final_Answer:
            image_path = "demo/6_generation.png"
        else:
            st.toast(f"Wrong OverviewImage status!")
            image_path = "demo/decompose_pipeline.png"

    return os.path.join(IMAGE_DIR, image_path)

################################################################################

def init_suite() -> None:
    with jsonlines.open(LOGGING_PATH, "r") as reader:
        state.testing_suite = [item for item in reader]


def get_logging_info(key: str, round_idx: int=None):
    if key == "answer":
        return state.qa_logging["answer"]

    if key == "answer_rationale":
        return state.qa_logging["answer_metadata"]["rationale"]

    if key == "answer_label":
        return state.qa_logging["answer_labels"][0]

    if key == "score":
        return state.qa_logging["answer_metric_scores"]["LLM-Accuracy"]

    if key == "supporting_fact_meta":
        chunks = list(set([sf["full_chunk"] for sf in state.qa_logging["metadata"]["supporting_facts"] if "full_chunk" in sf]))
        chunk_atoms = []
        for chunk in chunks:
            for sf in state.qa_logging["metadata"]["supporting_facts"]:
                if sf.get("full_chunk", "") == chunk:
                    chunk_atoms.append((chunk, sf.get("atomic_questions", None)))
        return chunk_atoms

    logging_meta = state.qa_logging["answer_metadata"]["decomposition_infos"]
    round_id = f"Sub{round_idx + 1}"

    if key == "round_info":
        return logging_meta.get(round_id, {})

    if key == "proposal_info":
        return logging_meta.get(round_id, {}).get("proposal", {})

    if key == "selection_info":
        return logging_meta.get(round_id, {}).get("selection", {})

    if key == "proposal_list":
        return logging_meta.get(round_id, {}).get("proposal", {}).get("proposal_list", [])

    if key == "retrieval_list":
        return logging_meta.get(round_id, {}).get("retrieval", [])

    if key == "chosen_chunk":
        return logging_meta.get(round_id, {}).get("selection", {}).get("chosen_info", {}).get("source_chunk", None)

    raise ValueError(f"Error key: {key}!")


def reset_info():
    state.context = []
    state.proposals = {}
    state.retrievals = []
    state.selection = {}
    state.terminated = False
    state.round_idx = 0
    state.cur_step = DecomposeStep.Initialization
    state.answer = None
    state.rationale = None

    qa_idx = 0
    for idx, qa in enumerate(state.testing_suite):
        if "question_selected" not in state or qa["question"] == state.question_selected:
            qa_idx = idx
            break
    state.qa_logging = state.testing_suite[qa_idx]

    state.overview_image = OverviewImage.DynamicPipeline


def highlight_context(c):
    for sf_dict in state.qa_logging["metadata"]["supporting_facts"]:
        if sf_dict["contents"] in c:
            return "color: #8A2BE2;"
    return ""


def highlight_atomic_question(q):
    for sf_dict in state.qa_logging["metadata"]["supporting_facts"]:
        for atomic_question in sf_dict.get("atomic_questions", []):
            if q.strip() == atomic_question.strip():
                return "color: #8A2BE2;"
    return ""

################################################################################

def go_atomic_proposal():
    state.cur_step = DecomposeStep.Propose_Atomic_Questions
    state.proposals = get_logging_info(key="proposal_info", round_idx=state.round_idx)


def go_atomic_retrieval():
    state.cur_step = DecomposeStep.Retrieve_Relevant_Atomic_Pairs

    if len(state.proposals["proposal_list"]) == 0:
        go_final_answer()
        return

    state.retrievals = get_logging_info(key="retrieval_list", round_idx=state.round_idx)

    if len(state.retrievals) == 0:
        go_final_answer()
        return


def go_atomic_selection():
    state.cur_step = DecomposeStep.Select_Most_Useful_Atomic_Question

    state.selection = get_logging_info(key="selection_info", round_idx=state.round_idx)

    if len(state.selection) == 0:
        go_final_answer()
        return


def go_update_context():
    state.cur_step = DecomposeStep.Update_Context

    newly_selected = state.selection.get("chosen_info", {}).get("source_chunk", None)
    if newly_selected is None:
        go_final_answer()
        return
    else:
        state.context.append(newly_selected)


def go_final_answer():
    state.cur_step = DecomposeStep.Generate_Final_Answer
    state.answer = get_logging_info(key="answer")
    state.rationale = get_logging_info(key="answer_rationale")
    state.terminated = True


def move_forward():
    if state.cur_step == DecomposeStep.Initialization:
        go_atomic_proposal()

    elif state.cur_step == DecomposeStep.Propose_Atomic_Questions:
        if len(state.proposals["proposal_list"]) > 0:
            go_atomic_retrieval()
        else:
            go_final_answer()

    elif state.cur_step == DecomposeStep.Retrieve_Relevant_Atomic_Pairs:
        if len(state.retrievals) > 0:
            go_atomic_selection()
        else:
            go_final_answer()

    elif state.cur_step == DecomposeStep.Select_Most_Useful_Atomic_Question:
        if state.selection.get("chosen_info", {}).get("source_chunk", None) is not None:
            go_update_context()
        else:
            go_final_answer()

    elif state.cur_step == DecomposeStep.Update_Context:
        if len(get_logging_info(key="round_info", round_idx=state.round_idx + 1)) == 0:
            go_final_answer()

        else:
            state.round_idx += 1
            state.proposals = {}
            state.retrievals = []
            state.selection = {}

            go_atomic_proposal()

    return

################################################################################

def on_next_step_click():
    move_forward()
    state.overview_image = OverviewImage.FollowDecomposeStep


def on_run_a_round_click():
    move_forward()
    while state.cur_step < 6:
        move_forward()

    state.overview_image = OverviewImage.DynamicPipeline


def on_run_to_end_click():
    while state.terminated is False:
        move_forward()

    state.overview_image = OverviewImage.DynamicPipeline


def on_decompose_image_click():
    state.overview_image = OverviewImage.DynamicPipeline


def on_data_collection_image_click():
    state.overview_image = OverviewImage.DynamicDataCollection


def on_decomposer_train_image_click():
    state.overview_image = OverviewImage.DynamicDecomposerTrain


def on_decomposer_train_click():
    state.overview_image = OverviewImage.DynamicDecomposerTrain


def on_dump_trajectory_click():
    state.overview_image = OverviewImage.DynamicDataCollection

################################################################################

def control_panel():
    with st.container():
        init_suite()

        if "terminated" not in state:
            reset_info()

        button_cols = st.columns(2)

        # Reset
        button_cols[0].button(
            ":orange[**Reset**]",
            on_click=reset_info,
            disabled=(state.cur_step == DecomposeStep.Initialization),
            use_container_width=True,
        )

        # Next Step
        button_cols[1].button(
            ":orange[**Next Step**]",
            on_click=on_next_step_click,
            disabled=state.terminated,
            use_container_width=True,
        )

        # Run one round
        button_cols[0].button(
            ":orange[**Run a Round**]",
            on_click=on_run_a_round_click,
            disabled=state.terminated,
            use_container_width=True,
        )


        # Run all button
        button_cols[1].button(
            ":orange[**Run to End**]",
            on_click=on_run_to_end_click,
            disabled=state.terminated,
            use_container_width=True,
        )


def context_and_answer_window():
    with st.container(border=True):
        result_cols = st.columns([1, 2])

        result_cols[0].markdown(f"**:violet[Round {state.round_idx + 1} [{step2str(state.cur_step)}]]**")
        result_cols[0].markdown("")

        result_cols[0].markdown(":violet[**Final Answer**]")
        if state.answer is not None:
            answer_cols = result_cols[0].columns([4, 2])
            answer_cols[0].markdown(state.answer)
            if state.answer == get_logging_info("answer"):
                if get_logging_info("score") == 1:
                    answer_cols[1].markdown(":violet[**✅CORRECT!**]")
                else:
                    answer_cols[1].markdown(":violet[**❎WRONG!**]")
        else:
            result_cols[0].markdown("")

        result_cols[0].markdown(":violet[**Rationale**]")
        if state.rationale is not None:
            result_cols[0].markdown(state.rationale)
        else:
            result_cols[0].markdown("")

        context_tab, atomic_tab = result_cols[1].tabs([":violet[**Context**]", ":violet[**Atomic Questions**]"])
        if len(state.context) > 0:
            context_tab.markdown(
                pd.DataFrame(state.context, columns=["Context"]).style.map(highlight_context).to_html(),
                unsafe_allow_html=True,
            )
            context_tab.markdown("")
            context_tab.markdown("*NOTE: The :violet[**supporting facts**] are displayed in violet.*")

            atomic_tab.markdown(
                pd.DataFrame(
                    [
                        get_logging_info(key="selection_info", round_idx=idx)["chosen_info"]["question"]
                        for idx in range(len(state.context))
                    ],
                    columns=["Context"],
                ).style.map(highlight_atomic_question).to_html(),
                unsafe_allow_html=True,
            )
            atomic_tab.markdown("")
            atomic_tab.markdown("*NOTE: The :violet[**atomic question linking to supporting facts**] are displayed in violet.*")


def show_proposals(proposal_data, retrieval_data, selection_data):
    def highlight_proposal(p):
        chosen_question = selection_data.get("chosen_info", {}).get("question", "")
        for retrieval_dict in retrieval_data:
            if retrieval_dict["sub-question"] == chosen_question and retrieval_dict["relevant_proposal"] == p:
                return "color: #8A2BE2;"
        return ""

    if len(proposal_data) > 0:
        tab1, tab2 = st.tabs([":violet[**Proposals**]", ":violet[**Rationale**]"])

        proposal_list = proposal_data.get("proposal_list", [])
        if len(proposal_list) > 0:
            tab1.markdown(
                pd.DataFrame(proposal_list, columns=["Proposal"]).style.map(highlight_proposal).to_html(),
                unsafe_allow_html=True,
            )
            tab1.markdown("")
            tab1.markdown("*NOTE: the proposals :violet[relevant to selected atomic question] are displayed in violet.*")
        else:
            tab1.markdown("📢No valid atomic question proposal. Terminate to generate answer directly...")

        tab2.markdown(proposal_data["thinking"])


def atomic_proposal_window():
    with st.container(border=True):
        st.subheader(":violet[**💡Atomic Proposal**]", anchor="_atomic_proposal")
        show_proposals(state.proposals, state.retrievals, state.selection)


def history_atomic_proposal_window(round_idx: int):
    with st.container(border=True):
        st.subheader(":violet[**💡Atomic Proposal**]")
        show_proposals(
            proposal_data=get_logging_info(key="proposal_info", round_idx=round_idx),
            retrieval_data=get_logging_info(key="retrieval_list", round_idx=round_idx),
            selection_data=get_logging_info(key="selection_info", round_idx=round_idx),
        )


def show_retrievals(proposal_data, retrieval_data, selection_data, round_idx):
    if len(retrieval_data) > 0:
        chosen_question = selection_data.get("chosen_info", {}).get("question", "")
        default_idx = 0
        for idx, retrieval_dict in enumerate(retrieval_data):
            if retrieval_dict["sub-question"] == chosen_question:
                default_idx = idx
                break
        st.selectbox(label=":violet[Select Result Index]:", options=range(len(retrieval_data)), key=f"{round_idx}_retrieval_idx", index=default_idx)
        if round_idx == state.round_idx:
            state.retrieval_idx = state[f"{round_idx}_retrieval_idx"]

        retrieval_dict = retrieval_data[state[f"{round_idx}_retrieval_idx"]]
        for proposal_idx, proposal in enumerate(proposal_data["proposal_list"]):
            if retrieval_dict["relevant_proposal"] == proposal:
                break
        st.markdown(f":violet[- Proposal Question (Index]: {proposal_idx}:violet[)]")
        st.markdown(proposal)
        st.markdown(":violet[- Relevant Atomic Question]")
        st.markdown(retrieval_dict["sub-question"])
        st.markdown(":violet[- Relevant Chunk]")
        st.markdown(retrieval_dict["relevant_context"])


def atomic_retrieval_window():
    with st.container(border=True):
        st.subheader(":violet[**🔎Retrieval**]", anchor="_retrieval")
        show_retrievals(state.proposals, state.retrievals, state.selection, state.round_idx)


def history_atomic_retrieval_window(round_idx: int):
    with st.container(border=True):
        st.subheader(":violet[**🔎Retrieval**]")
        show_retrievals(
            proposal_data=get_logging_info(key="proposal_info", round_idx=round_idx),
            retrieval_data=get_logging_info(key="retrieval_list", round_idx=round_idx),
            selection_data=get_logging_info(key="selection_info", round_idx=round_idx),
            round_idx=round_idx,
        )


def show_selection(selection_data):
    if len(selection_data) > 0:
        tab1, tab2 = st.tabs([":violet[**Selection Info**]", ":violet[**Rationale**]"])

        if len(selection_data.get("chosen_info", {})) > 0:
            chosen_info = selection_data["chosen_info"]

            tab1.markdown(":violet[- Atomic Question]")
            tab1.markdown(chosen_info["question"])

            if chosen_info["source_chunk_title"] is not None:
                tab1.markdown(":violet[- Chunk Title]")
                tab1.markdown(chosen_info["source_chunk_title"])

            tab1.markdown(":violet[- Chunk]")
            tab1.markdown(chosen_info["source_chunk"])

        else:
            tab1.markdown("📢No valid atomic question selection. Terminate to generate answer directly...")

        tab2.markdown(selection_data["thinking"])


def atomic_selection_window():
    with st.container(border=True):
        st.subheader(":violet[**⚖️Selection**]", anchor="_selection")
        show_selection(state.selection)


def history_atomic_selection_window(round_idx: int):
    with st.container(border=True):
        st.subheader(":violet[**⚖️Selection**]")
        show_selection(
            selection_data=get_logging_info(key="selection_info", round_idx=round_idx)
        )

################################################################################

st.set_page_config(layout="wide", page_title="PIKE-RAG", page_icon=ICON_PATH, initial_sidebar_state="expanded")

with st.sidebar:
    logo_cols = st.columns([3, 2], gap="small", vertical_alignment="bottom")
    logo_cols[0].image(LOGO_PATH)
    logo_cols[1].markdown("[:grey[@GitHub]](https://github.com/microsoft/PIKE-RAG)")

    st.subheader(":blue[Table of Content]", divider="blue")
    st.markdown(table_of_content)

    st.markdown("")
    st.subheader(":orange[Control Panel]", divider="orange")
    control_panel()

    st.markdown("")
    st.subheader(":violet[Domain-Alignment Panel]", divider="violet")
    st.button(
        ":violet[**Save User Interaction Trajectory**]",
        on_click=on_dump_trajectory_click,
        use_container_width=True,
    )
    st.button(
        ":violet[**Fine-Tune Proposer w/ Trajectories**]",
        on_click=on_decomposer_train_click,
        use_container_width=True,
    )

    st.markdown("")
    st.subheader(":green[Technical Report]", divider="green")
    st.markdown("### [:green[🎓PIKE-RAG @arXiv]](https://arxiv.org/abs/2501.11551)")

st.title("sPecIalized KnowledgE and Rationale Augmented Generation")

# Overview Diagram
st.header("📊Approach Overview", divider="blue", anchor="_overview")
with st.container():
    _, main_col, _ = st.columns([0.4, 8, 0.4])
    button_cols = main_col.columns(3)
    button_cols[0].button(label=":blue[**🧠Task Decomposition**]", on_click=on_decompose_image_click, use_container_width=True)
    button_cols[1].button(label=":blue[**🧩Data Collection**]", on_click=on_data_collection_image_click, use_container_width=True)
    button_cols[2].button(label=":blue[**💫Decomposer Training**]", on_click=on_decomposer_train_image_click, use_container_width=True)

    image_path = get_overview_image_path()
    if state.overview_image == OverviewImage.FollowDecomposeStep:
        main_col.image(image_path)
    else:
        with open(image_path, "rb") as image_file:
            contents = image_file.read()
            data_url = base64.b64encode(contents).decode("utf-8")
        main_col.markdown(f'<img src="data:image/gif;base64,{data_url}" alt="overview">', unsafe_allow_html=True)

# Choose question for decomposition and answering.
st.header("⚙️QA Selection", divider="orange", anchor="_qa")
with st.container(border=True):
    st.selectbox(
        key="question_selected",
        label=":orange[**Question**]",
        help="Select the question you want to demonstrate from the drop-down list.",
        options=[qa["question"] for qa in state.testing_suite],
        index=0,
        on_change=reset_info,
    )
    st.text_input(label=":orange[**Ground-Truth Answer of this Question**]", value=get_logging_info(key="answer_label"), disabled=True)

    sf_chunks = get_logging_info(key="supporting_fact_meta")
    if st.toggle(label=":orange[**Show Supporting Facts Meta**]", value=False, key="show_sf_meta"):
        if len(sf_chunks) > 0:
            tabs = st.tabs([f":orange[**Meta-{i + 1}**]" for i in range(len(sf_chunks))])
            for tab, (full_chunk, atoms) in zip(tabs, sf_chunks):
                tab.markdown(f":orange[**Full Chunk**]: {full_chunk}")
                tab.table(pd.DataFrame(atoms, columns=["Atomic Question"]))

# Workflow step by step
st.header("🧠Decomposition Demonstration", divider="violet", anchor="_workflow")
with st.container():
    context_and_answer_window()

    tabs = st.tabs(
        [f"**:violet[Current Round]**"] + [f"**:violet[Round {state.round_idx - idx}]**" for idx in range(state.round_idx)]
    )

    # Show current round in tab-0
    col1, col2, col3 = tabs[0].columns(3)
    with col1:
        atomic_proposal_window()
    with col2:
        atomic_retrieval_window()
    with col3:
        atomic_selection_window()

    # Previous tabs show historical infos
    for idx, tab in enumerate(tabs[1:]):
        round_idx = state.round_idx - idx - 1

        tc1, tc2, tc3 = tab.columns(3)
        with tc1:
            history_atomic_proposal_window(round_idx)
        with tc2:
            history_atomic_retrieval_window(round_idx)
        with tc3:
            history_atomic_selection_window(round_idx)
