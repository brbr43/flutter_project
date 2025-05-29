class Tennisbooking {
  final int id;
  final int userId;
  final String reservationDate;
  final String startTime;
  final String endTime;
  final String createdAt;
  final String updatedAt;
  final String email;

  Tennisbooking({
    required this.id,
    required this.userId,
    required this.reservationDate,
    required this.startTime,
    required this.endTime,
    required this.createdAt,
    required this.updatedAt,
    required this.email,
  });

  // تحويل الـ JSON إلى كائن من النوع GymBooking
  factory Tennisbooking.fromJson(Map<String, dynamic> json) {
    return Tennisbooking(
      id: json['id'],
      userId: json['user_id'],
      reservationDate: json['reservation_date'],
      startTime: json['start_time'],
      endTime: json['end_time'],
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
      'reservation_date': reservationDate,
      'start_time': startTime,
      'end_time': endTime,
      'created_at': createdAt,
      'updated_at': updatedAt,
      'email': email,
    };
  }
}
