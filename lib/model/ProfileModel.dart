class ProfileModel {
  final int id;
  final String email;
  final String phoneNumber;
  final int apartmentNumber;
  final String complexName;

  ProfileModel({
    required this.id,
    required this.email,
    required this.phoneNumber,
    required this.apartmentNumber,
    required this.complexName,
  });

  factory ProfileModel.fromJson(Map<String, dynamic> json) {
    return ProfileModel(
      id: json['id'],
      email: json['email'],
      phoneNumber: json['phone_number'],
      apartmentNumber: json['apartment_number'],
      complexName: json['complex_name'],
    );
  }
}
