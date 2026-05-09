import json
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Agent Access Governance Simulator",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Agent Access Governance Simulator")
st.markdown(
    "**Block AI agent actions when the agent is unauthorized — "
    "or when the target data is untrustworthy.**  \n"
    "Three-layer governance: identity → policy → data quality. "
    "All three must pass before an agent action proceeds."
)
st.divider()

# ── Registry data ──────────────────────────────────────────────────────────────
AGENTS = {
    "analytics-agent":  {"role": "analyst",  "allowed_actions": ["read", "aggregate", "export"]},
    "pipeline-agent":   {"role": "engineer", "allowed_actions": ["read", "write", "transform"]},
    "reporting-agent":  {"role": "analyst",  "allowed_actions": ["read", "export"]},
    "admin-agent":      {"role": "admin",    "allowed_actions": ["read","write","delete","export","transform","aggregate"]},
    "unknown-agent":    {"role": "unknown",  "allowed_actions": []},
}

DATASETS = {
    "sales_metrics": {
        "owner": "analytics-team",
        "quality_score": 0.94,
        "last_updated_hours_ago": 2,
        "freshness_threshold_hours": 24,
        "failed_tests": [],
        "required_roles": ["analyst", "engineer", "admin"],
    },
    "user_events": {
        "owner": "data-engineering",
        "quality_score": 0.71,
        "last_updated_hours_ago": 36,
        "freshness_threshold_hours": 24,
        "failed_tests": ["row_count_check", "null_check_user_id"],
        "required_roles": ["engineer", "admin"],
    },
    "clean_pipeline_table": {
        "owner": "data-engineering",
        "quality_score": 0.98,
        "last_updated_hours_ago": 0.5,
        "freshness_threshold_hours": 6,
        "failed_tests": [],
        "required_roles": ["analyst", "engineer", "admin"],
    },
    "stale_report_cache": {
        "owner": "reporting-team",
        "quality_score": 0.45,
        "last_updated_hours_ago": 72,
        "freshness_threshold_hours": 12,
        "failed_tests": ["freshness_check", "schema_validation", "null_check_date"],
        "required_roles": ["analyst", "admin"],
    },
    "experimental_features_log": {
        "owner": "product-team",
        "quality_score": 0.83,
        "last_updated_hours_ago": 4,
        "freshness_threshold_hours": 48,
        "failed_tests": ["duplicate_check"],
        "required_roles": ["admin"],
    },
}

QUALITY_THRESHOLD = 0.80

# ── Governance engine ──────────────────────────────────────────────────────────
def check_governance(agent_name, action, dataset_name, qs, freshness_h, failed_tests):
    agent   = AGENTS.get(agent_name)
    dataset = DATASETS.get(dataset_name)

    audit = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent":     agent_name,
        "action":    action,
        "dataset":   dataset_name,
        "checks":    {},
        "decision":  None,
        "reason":    None,
    }

    # Layer 1 — Identity
    identity_ok = agent is not None and agent["role"] != "unknown"
    audit["checks"]["identity"] = {
        "pass":   identity_ok,
        "detail": (
            f"Agent '{agent_name}' registered with role '{agent['role']}'"
            if identity_ok else
            f"Agent '{agent_name}' is unknown or unregistered"
        ),
    }
    if not identity_ok:
        audit["decision"] = "BLOCKED"
        audit["reason"]   = "Identity check failed — unknown or unregistered agent"
        return audit

    # Layer 2 — Policy
    action_ok = action in agent["allowed_actions"]
    role_ok   = agent["role"] in dataset["required_roles"]
    policy_ok = action_ok and role_ok

    audit["checks"]["policy"] = {
        "pass":   policy_ok,
        "detail": (
            f"Action '{action}' {'✓ permitted' if action_ok else '✗ not permitted'} for role '{agent['role']}' | "
            f"Role '{agent['role']}' {'✓ authorized' if role_ok else '✗ not authorized'} for this dataset"
        ),
    }
    if not policy_ok:
        audit["decision"] = "BLOCKED"
        audit["reason"] = (
            "Policy check failed — "
            + ("action not permitted for this agent's role"
               if not action_ok else "agent's role is not authorized for this dataset")
        )
        return audit

    # Layer 3 — Data Quality
    is_fresh   = freshness_h <= dataset["freshness_threshold_hours"]
    meets_qual = qs >= QUALITY_THRESHOLD
    no_fails   = len(failed_tests) == 0
    quality_ok = is_fresh and meets_qual and no_fails

    audit["checks"]["data_quality"] = {
        "pass":               quality_ok,
        "quality_score":      qs,
        "quality_threshold":  QUALITY_THRESHOLD,
        "quality_ok":         meets_qual,
        "freshness_hours":    freshness_h,
        "freshness_threshold":dataset["freshness_threshold_hours"],
        "is_fresh":           is_fresh,
        "failed_tests":       failed_tests,
        "no_failed_tests":    no_fails,
    }

    if not quality_ok:
        reasons = []
        if not meets_qual: reasons.append(f"quality score {qs:.2f} < threshold {QUALITY_THRESHOLD}")
        if not is_fresh:   reasons.append(f"data {freshness_h}h old (limit: {dataset['freshness_threshold_hours']}h)")
        if not no_fails:   reasons.append(f"failed tests: {', '.join(failed_tests)}")
        audit["decision"] = "BLOCKED"
        audit["reason"]   = "Data quality check failed — " + "; ".join(reasons)
        return audit

    audit["decision"] = "ALLOWED"
    audit["reason"]   = "All checks passed — identity, policy, and data quality verified"
    return audit

# ── UI ────────────────────────────────────────────────────────────────────────
col_cfg, col_result = st.columns([1, 1.8])

with col_cfg:
    st.subheader("⚙️ Scenario Configuration")

    PRESETS = {
        "Custom (manual)": None,
        "✅ Analyst reads clean data":           ("analytics-agent",  "read",   "clean_pipeline_table"),
        "🚫 Analyst tries to delete":            ("analytics-agent",  "delete", "sales_metrics"),
        "⚠️ Pipeline agent reads stale cache":   ("pipeline-agent",   "read",   "stale_report_cache"),
        "🚫 Unknown agent":                       ("unknown-agent",    "read",   "sales_metrics"),
        "⚠️ Engineer reads dataset with failures":("pipeline-agent",  "read",   "user_events"),
    }

    preset = st.selectbox("Quick Preset", list(PRESETS.keys()))
    p = PRESETS[preset]

    agent_list   = list(AGENTS.keys())
    dataset_list = list(DATASETS.keys())
    action_list  = ["read", "write", "delete", "export", "transform", "aggregate"]

    agent_name   = st.selectbox("Agent",   agent_list,   index=agent_list.index(p[0])   if p else 0)
    action       = st.selectbox("Action",  action_list,  index=action_list.index(p[1])  if p else 0)
    dataset_name = st.selectbox("Dataset", dataset_list, index=dataset_list.index(p[2]) if p else 0)

    d = DATASETS[dataset_name]
    st.markdown("**Override Data Quality Parameters**")
    st.caption("Defaults match the registered values. Adjust to explore edge cases.")

    override_qs       = st.slider("Quality Score",            0.0, 1.0, float(d["quality_score"]),           0.01)
    override_fresh    = st.slider("Hours Since Last Update",  0.0, 100.0, float(d["last_updated_hours_ago"]), 0.5)

    all_tests = [
        "row_count_check", "null_check_user_id", "freshness_check",
        "schema_validation", "null_check_date", "duplicate_check",
    ]
    override_tests = st.multiselect("Failed Tests", all_tests, default=d["failed_tests"])

    check_btn = st.button("🛡️ Run Governance Check", type="primary", use_container_width=True)

with col_result:
    st.subheader("🔍 Governance Decision")

    if not check_btn:
        st.info("Configure a scenario and click **Run Governance Check**.")
        st.markdown(
            """
            **The three layers:**

            **Layer 1 — Identity**  
            Is this agent registered and recognized by the governance system?

            **Layer 2 — Policy**  
            Does this agent's role permit this action on this dataset?

            **Layer 3 — Data Quality**  
            Is the target dataset fresh, passing all quality tests, and above the quality threshold?

            All three must pass. A policy-authorized agent can still be blocked
            if the data it wants to act on is stale or failing checks.
            """
        )
    else:
        result = check_governance(
            agent_name, action, dataset_name,
            override_qs, override_fresh, override_tests,
        )

        if result["decision"] == "ALLOWED":
            st.success("### ✅ ALLOWED")
        else:
            st.error("### 🚫 BLOCKED")

        st.markdown(f"**Reason:** {result['reason']}")
        st.divider()
        st.markdown("#### Check-by-Check Breakdown")

        checks = result["checks"]

        id_c = checks.get("identity", {})
        icon = "✅" if id_c.get("pass") else "❌"
        with st.expander(f"{icon} Layer 1 — Identity Check", expanded=True):
            st.markdown(id_c.get("detail", "—"))

        pol_c = checks.get("policy", {})
        if pol_c:
            icon = "✅" if pol_c.get("pass") else "❌"
            with st.expander(f"{icon} Layer 2 — Policy Check", expanded=True):
                st.markdown(pol_c.get("detail", "—"))

        dq_c = checks.get("data_quality", {})
        if dq_c:
            icon = "✅" if dq_c.get("pass") else "❌"
            with st.expander(f"{icon} Layer 3 — Data Quality Check", expanded=True):
                m1, m2, m3 = st.columns(3)
                m1.metric(
                    "Quality Score",
                    f"{dq_c['quality_score']:.2f}",
                    f"Threshold ≥ {dq_c['quality_threshold']}",
                    delta_color="normal" if dq_c["quality_ok"] else "inverse",
                )
                m2.metric(
                    "Data Age",
                    f"{dq_c['freshness_hours']}h",
                    f"Limit: {dq_c['freshness_threshold']}h",
                    delta_color="normal" if dq_c["is_fresh"] else "inverse",
                )
                m3.metric(
                    "Failed Tests",
                    len(dq_c["failed_tests"]),
                    "Must be 0",
                    delta_color="normal" if dq_c["no_failed_tests"] else "inverse",
                )
                if dq_c["failed_tests"]:
                    st.error("Failed: " + ", ".join(f"`{t}`" for t in dq_c["failed_tests"]))

        st.divider()
        st.markdown("#### Audit Log")
        st.json(result)
        st.download_button(
            "⬇️ Download Audit Log (JSON)",
            data=json.dumps(result, indent=2),
            file_name=f"audit_{agent_name}_{action}_{dataset_name}.json",
            mime="application/json",
        )