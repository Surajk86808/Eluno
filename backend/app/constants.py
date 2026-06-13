LENS_TYPES = ["Single Vision", "Progressive", "Bifocal"]

ORDER_STATUSES = [
    "Order Placed",
    "Prescription Verified",
    "Lens Cutting",
    "Coating",
    "Frame Fitting",
    "Quality Check",
    "Packing",
    "Shipped",
    "Delivered",
]

TERMINAL_STATUSES = {"Shipped", "Delivered"}

SLA_HOURS_BY_LENS_TYPE = {
    "Single Vision": 24,
    "Bifocal": 48,
    "Progressive": 72,
}

STORE_LOCATIONS = [
    "Bangalore",
    "Chennai",
    "Delhi",
    "Hyderabad",
    "Kolkata",
    "Mumbai",
    "Pune",
]

DELAY_REASONS = [
    "Inventory Shortage",
    "Logistics Delay",
    "Machine Breakdown",
    "None",
    "QC Failure",
    "Supplier Delay",
]
