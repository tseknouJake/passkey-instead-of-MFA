"""
User study routes.

Users complete the study for the login method they most recently used.
"""

from flask import Blueprint, redirect, render_template, request, session, url_for

from modules.services.study_service import (
    GENDER_OPTIONS,
    LIKERT_QUESTIONS,
    StudyStorageSetupError,
    TECHNICAL_EXPERTISE_OPTIONS,
    USED_BEFORE_OPTIONS,
    get_auth_method_label,
    get_study_profile,
    get_study_response,
    save_study_profile,
    save_study_response,
)
from modules.utils.decorators import login_required

study = Blueprint("study", __name__, url_prefix="/study")


def _merge_form_data(profile: dict | None, response: dict | None) -> dict:
    merged = {}
    if profile:
        merged.update(profile)
    if response:
        merged.update(response)
    return merged


def _validate_study_submission(form) -> tuple[dict, dict, str | None]:
    age_raw = (form.get("age") or "").strip()
    gender = (form.get("gender") or "").strip()
    technical_expertise_raw = (form.get("technical_expertise") or "").strip()
    used_before = (form.get("used_before") or "").strip()
    additional_feedback = (form.get("additional_feedback") or "").strip()

    form_data = {
        "age": age_raw,
        "gender": gender,
        "technical_expertise": technical_expertise_raw,
        "used_before": used_before,
        "additional_feedback": additional_feedback,
    }

    if not age_raw.isdigit():
        return {}, form_data, "Age must be a whole number."

    age = int(age_raw)
    if age < 13 or age > 120:
        return {}, form_data, "Age must be between 13 and 120."

    if gender not in GENDER_OPTIONS:
        return {}, form_data, "Please select a gender option."

    if not technical_expertise_raw.isdigit():
        return {}, form_data, "Technical expertise must be a number from 1 to 5."

    technical_expertise = int(technical_expertise_raw)
    if technical_expertise < 1 or technical_expertise > 5:
        return {}, form_data, "Technical expertise must be between 1 and 5."

    if used_before not in {"yes", "no"}:
        return {}, form_data, "Please answer whether you used this login method before today."

    response_data = {"used_before": used_before == "yes", "additional_feedback": additional_feedback}

    for key, _label in LIKERT_QUESTIONS:
        raw_value = (form.get(key) or "").strip()
        form_data[key] = raw_value

        if not raw_value.isdigit():
            return {}, form_data, "Please answer every study statement on the 1 to 5 scale."

        value = int(raw_value)
        if value < 1 or value > 5:
            return {}, form_data, "Study answers must be between 1 and 5."

        response_data[key] = value

    validated = {
        "profile": {
            "age": age,
            "gender": gender,
            "technical_expertise": technical_expertise,
        },
        "response": response_data,
    }
    return validated, form_data, None


@study.route("/", methods=["GET", "POST"])
@login_required
def user_study():
    username = session["username"]
    auth_method = session.get("auth_method")

    if not auth_method:
        return redirect(url_for("main.dashboard"))

    auth_method_label = get_auth_method_label(auth_method)
    try:
        profile = get_study_profile(username)
        response = get_study_response(username, auth_method)
    except StudyStorageSetupError as exc:
        return render_template(
            "user_study.html",
            error=None,
            saved=False,
            form_data={},
            auth_method=auth_method,
            auth_method_label=auth_method_label,
            likert_questions=LIKERT_QUESTIONS,
            technical_expertise_options=TECHNICAL_EXPERTISE_OPTIONS,
            gender_options=GENDER_OPTIONS,
            used_before_options=USED_BEFORE_OPTIONS,
            completed=False,
            study_available=False,
            study_error=str(exc),
        )

    if request.method == "POST":
        validated, form_data, error = _validate_study_submission(request.form)
        if error:
            return render_template(
                "user_study.html",
                error=error,
                saved=False,
                form_data=form_data,
                auth_method=auth_method,
                auth_method_label=auth_method_label,
                likert_questions=LIKERT_QUESTIONS,
                technical_expertise_options=TECHNICAL_EXPERTISE_OPTIONS,
                gender_options=GENDER_OPTIONS,
                used_before_options=USED_BEFORE_OPTIONS,
                completed=response is not None,
                study_available=True,
                study_error=None,
            )

        try:
            save_study_profile(username, validated["profile"])
            save_study_response(username, auth_method, validated["response"])
        except StudyStorageSetupError as exc:
            return render_template(
                "user_study.html",
                error=None,
                saved=False,
                form_data=form_data,
                auth_method=auth_method,
                auth_method_label=auth_method_label,
                likert_questions=LIKERT_QUESTIONS,
                technical_expertise_options=TECHNICAL_EXPERTISE_OPTIONS,
                gender_options=GENDER_OPTIONS,
                used_before_options=USED_BEFORE_OPTIONS,
                completed=response is not None,
                study_available=False,
                study_error=str(exc),
            )
        return redirect(url_for("study.user_study", saved=1))

    form_data = _merge_form_data(profile, response)
    return render_template(
        "user_study.html",
        error=None,
        saved=request.args.get("saved") == "1",
        form_data=form_data,
        auth_method=auth_method,
        auth_method_label=auth_method_label,
        likert_questions=LIKERT_QUESTIONS,
        technical_expertise_options=TECHNICAL_EXPERTISE_OPTIONS,
        gender_options=GENDER_OPTIONS,
        used_before_options=USED_BEFORE_OPTIONS,
        completed=response is not None,
        study_available=True,
        study_error=None,
    )
