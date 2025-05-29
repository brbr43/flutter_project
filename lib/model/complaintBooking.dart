class Complaintbooking {
  final int id;
  final int userId;
  final String message;
  final String createdAt;
  final String updatedAt;
  final String email;

  Complaintbooking({
    required this.id,
    required this.userId,
    required this.message,
    required this.createdAt,
    required this.updatedAt,
    required this.email,
  });

  // تحويل الـ JSON إلى كائن من النوع Complaint
  factory Complaintbooking.fromJson(Map<String, dynamic> json) {
    return Complaintbooking(
      id: json['id'],
      userId: json['user_id'],
      message: json['message'],
      createdAt: json['created_at'],
      updatedAt: json['updated_at'],
      email: json['email'],
    );
  }

  // تحويل الكائن إلى JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'message': message,
      'created_at': createdAt,
      'updated_at': updatedAt,
      'email': email,
    };
  }
}
