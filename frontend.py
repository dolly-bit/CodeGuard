
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="CodeGuard AI",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ CodeGuard AI")
st.subheader("Repository-aware debugging assistant")
st.write(
    "Submit a bug report and source files to retrieve "
    "the code most relevant to the problem."
)

with st.form("analyze_form"):
    bug_report = st.text_area(
        "Bug report",
        placeholder="Describe the error, stack trace, or unexpected behavior...",
        height=160,
    )

    uploaded_files = st.file_uploader(
        "Upload source files",
        type=["py"],
        accept_multiple_files=True,
    )

    top_k = st.slider(
        "Evidence chunks to retrieve",
        min_value=1,
        max_value=10,
        value=3,
    )

    submitted = st.form_submit_button(
        "Analyze bug",
        type="primary",
    )

if submitted:
    if not bug_report.strip():
        st.error("Enter a bug report first.")
    elif not uploaded_files:
        st.error("Upload at least one Python source file.")
    else:
        files_payload = []

        for uploaded_file in uploaded_files:
            try:
                content = uploaded_file.getvalue().decode("utf-8")
            except UnicodeDecodeError:
                st.error(
                    f"{uploaded_file.name} is not valid UTF-8 text."
                )
                st.stop()

            files_payload.append(
                {
                    "path": uploaded_file.name,
                    "content": content,
                }
            )

        try:
            with st.spinner("Retrieving relevant code..."):
                response = requests.post(
                    f"{API_URL}/analyze",
                    json={
                        "bug_report": bug_report,
                        "files": files_payload,
                        "top_k": top_k,
                    },
                    timeout=30,
                )

            response.raise_for_status()
            result = response.json()

            st.success("Analysis request completed")
            st.caption(
                f"Mode: {result.get('mode', 'unknown')}"
            )

            if result.get("notice"):
                st.info(result["notice"])

            evidence = result.get("evidence", [])

            if not evidence:
                st.warning("No relevant code evidence was found.")

            for index, item in enumerate(evidence, start=1):
                heading = (
                    f"{index}. {item['path']} "
                    f"(lines {item['start_line']}-"
                    f"{item['end_line']})"
                )

                with st.expander(heading, expanded=(index == 1)):
                    st.metric(
                        "Similarity score",
                        item["similarity_score"],
                    )
                    st.code(
                        item["content"],
                        language="python",
                    )

                    st.caption(
                        item.get("score_interpretation", "")
                    )

        except requests.RequestException as exc:
            st.error(
                "Could not contact CodeGuard AI. "
                "Check that the FastAPI backend is running "
                "at http://127.0.0.1:8000."
            )
            st.caption(str(exc))
