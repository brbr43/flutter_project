class PartyBooking {
  final int id;
  final int userId;
  final String partyDate;
  final String reason;
  final int guestsCount;
  final String startTime;
  final String endTime;
  final String createdAt;
  final String updatedAt;
  final String email;

  PartyBooking({
    required this.id,
    required this.userId,
    required this.partyDate,
    required this.reason,
    required this.guestsCount,
    required this.startTime,
    required this.endTime,
    required this.createdAt,
    required this.updatedAt,
    required this.email,
  });

  // تحويل الـ JSON إلى كائن PartyBooking
  factory PartyBooking.fromJson(Map<String, dynamic> json) {
    return PartyBooking(
      id: json['id'],
      userId: json['user_id'],
      partyDate: json['party_date'],
      reason: json['reason'],
      guestsCount: json['guests_count'],
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
      'party_date': partyDate,
      'reason': reason,
      'guests_count': guestsCount,
      'start_time': startTime,
      'end_time': endTime,
      'created_at': createdAt,
      'updated_at': updatedAt,
      'email': email,
    };
  }
}
