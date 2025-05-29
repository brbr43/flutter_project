class User {
  final int id;
  final String email;
  final String? emailVerifiedAt;
  final String createdAt;
  final String updatedAt;
  final String phoneNumber;
  final int apartmentNumber;
  final String complexName;

  User({
    required this.id,
    required this.email,
    this.emailVerifiedAt,
    required this.createdAt,
    required this.updatedAt,
    required this.phoneNumber,
    required this.apartmentNumber,
    required this.complexName,
  });

  // من الـ JSON إلى كائن من نوع User
  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      emailVerifiedAt: json['email_verified_at'],
      createdAt: json['created_at'],
      updatedAt: json['updated_at'],
      phoneNumber: json['phone_number'],
      apartmentNumber: json['apartment_number'],
      complexName: json['complex_name'],
    );
  }
}
