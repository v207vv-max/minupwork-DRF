from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthenticatedAndClient(BasePermission):
    message = "Only clients can perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == "client"
        )


class IsAuthenticatedAndFreelancer(BasePermission):
    message = "Only freelancers can perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == "freelancer"
        )


class ProjectPermission(BasePermission):
    """
    Rules:
    - authenticated users can view projects
    - only clients can create projects
    - only project owner client can update project
    """

    message = "You do not have permission to access this project."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        if request.method == "POST":
            return getattr(user, "role", None) == "client"

        return getattr(user, "role", None) == "client"

    def has_object_permission(self, request, view, obj):
        user = request.user

        if request.method in SAFE_METHODS:
            return True

        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == "client"
            and obj.client_id == user.id
        )


class BidPermission(BasePermission):
    """
    Rules:
    - freelancers can create bids
    - client owner can view bids for own projects
    - freelancer owner can view own bids
    - only client owner can accept/reject a bid
    """

    message = "You do not have permission to access this bid."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if request.method == "POST":
            return getattr(user, "role", None) == "freelancer"

        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        action = getattr(view, "action", None)

        if action in {"accept", "reject"}:
            return bool(
                getattr(user, "role", None) == "client"
                and obj.project.client_id == user.id
            )

        if action in {"update", "partial_update", "withdraw"}:
            return bool(
                getattr(user, "role", None) == "freelancer"
                and obj.freelancer_id == user.id
            )

        return bool(
            obj.freelancer_id == user.id
            or obj.project.client_id == user.id
        )


class ProjectBidListPermission(BasePermission):
    """
    Only the client owner of the project can see bids for that project.
    """

    message = "Only the owner client can view bids for this project."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == "client"
        )

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) == "client"
            and obj.client_id == user.id
        )


class ContractPermission(BasePermission):
    """
    Rules:
    - client can see own contracts
    - freelancer can see own contracts
    - only client owner can finish a contract
    """

    message = "You do not have permission to access this contract."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        action = getattr(view, "action", None)

        if action == "finish":
            return bool(
                getattr(user, "role", None) == "client"
                and obj.client_id == user.id
            )

        return bool(
            obj.client_id == user.id
            or obj.freelancer_id == user.id
        )


class ReviewPermission(BasePermission):
    """
    Rules:
    - authenticated users can read reviews
    - only clients can create reviews
    - only review owner client can update own review
    """

    message = "You do not have permission to access this review."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return getattr(user, "role", None) == "client"

    def has_object_permission(self, request, view, obj):
        user = request.user

        if request.method in SAFE_METHODS:
            return True

        return bool(
            getattr(user, "role", None) == "client"
            and obj.client_id == user.id
        )
