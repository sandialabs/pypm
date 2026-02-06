from .matching_models import (
    GSF_TotalMatchScore,
    GSF_TotalMatchScore,
    GSF_TotalMatchScore_Compact,
    GSFED_TotalMatchScore,
    GSF_Makespan,
    XSF_TotalMatchScore,
    XSF_TotalMatchScore_Compact,
    UPM_TotalMatchScore,
)
#from .hmm_models import GSF_HMM, GSF_HMM_Compact, XSF_HMM, XSF_HMM_Compact


# -----------------------------------------------------------------------------------------------------
# The create_model() is the main function used externally to setup model objects.
# -----------------------------------------------------------------------------------------------------


def create_model(*, name, config, constraints):
    M = None

    if (
        name == "model11"
        or name == "GSF"
        or name == "UnrestrictedMatches_VariableLengthActivities_GapsAllowed"
    ):
        M = GSF_TotalMatchScore(gaps_allowed=True)

    elif name == "UnrestrictedMatches_VariableLengthActivities":
        M = GSF_TotalMatchScore(gaps_allowed=False)

    elif (
        name == "GSF-compact"
        or name == "GSFC"
        or name == "CompactMatches_VariableLengthActivities"
    ):
        M = GSF_TotalMatchScore_Compact()

    elif name == "model13" or name == "GSF-ED":
        M = GSFED_TotalMatchScore()

    elif name == "GSF-makespan":
        M = GSF_Makespan()

    elif name == "XSF" or name == "UnrestrictedMatches_FixedLengthActivities":
        M = XSF_TotalMatchScore()

    elif (
        name == "XSF-compact"
        or name == "XSFC"
        or name == "CompactMatches_FixedLengthActivities"
    ):
        M = XSF_TotalMatchScore_Compact()

    elif name == "model12" or name == "model14" or name == "UPM":
        M = UPM_TotalMatchScore()

    elif name == "HMM_UnrestrictedMatches_VariableLengthActivities_GapsAllowed":
        config.objective = "log_likelihood"
        M = GSF_HMM(gaps_allowed=True)

    elif name == "HMM_CompactMatches_VariableLengthActivities":
        config.objective = "log_likelihood"
        M = GSF_HMM_Compact()

    elif name == "HMM_UnrestrictedMatches_FixedLengthActivities":
        config.objective = "log_likelihood"
        M = XSF_HMM()

    elif name == "HMM_CompactMatches_FixedLengthActivities":
        config.objective = "log_likelihood"
        M = XSF_HMM_Compact()

    # Initialize the model object if it has been created
    if M is not None:
        M(config, constraints=constraints)

    return M
