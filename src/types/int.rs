use num::{BigInt, FromPrimitive};
use std::error::Error;
use std::str::FromStr;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ParseWenyanIntError {
    kind: WenyanIntErrorKind,
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum WenyanIntErrorKind {
    Empty,
    InvalidDigit,
    RedundantSign,
}

impl ParseWenyanIntError {
    fn __description(&self) -> &str {
        match self.kind {
            WenyanIntErrorKind::Empty => "cannot parse integer from empty string",
            WenyanIntErrorKind::InvalidDigit => "invalid digit found in string",
            WenyanIntErrorKind::RedundantSign => "redundant sign found in string",
        }
    }
}

impl std::fmt::Display for ParseWenyanIntError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.__description().fmt(f)
    }
}

impl Error for ParseWenyanIntError {
    fn description(&self) -> &str {
        self.__description()
    }
}

#[derive(Debug)]
pub struct WenyanInt {
    data: BigInt,
}

impl PartialEq for WenyanInt {
    fn eq(&self, other: &Self) -> bool {
        self.data == other.data
    }

    fn ne(&self, other: &Self) -> bool {
        self.data != other.data
    }
}

impl FromStr for WenyanInt {
    type Err = ParseWenyanIntError;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let mut result_vec: Vec<u8> = vec![];
        let mut chars = s.chars();
        let mut sign = 1;
        loop {
            match chars.next() {
                Some(c) => {
                    if c == '負' {
                        if sign == -1 {
                            return Err(Self::Err {
                                kind: WenyanIntErrorKind::RedundantSign,
                            });
                        }
                        sign = -1;
                    } else if "零一二三四五六七八九".contains(c) {
                        match "零一二三四五六七八九".chars().position(|chr| chr == c) {
                            Some(0) => {
                                if result_vec.len() == 0 {
                                    if chars.next().is_some() {
                                        return Err(Self::Err {
                                            kind: WenyanIntErrorKind::InvalidDigit,
                                        });
                                    }
                                    result_vec.push(48);
                                }
                            }
                            Some(d) => {
                                result_vec.push(d as u8 + 48);
                            }
                            None => {}
                        }
                    } else if "十".contains(c) {
                    } else {
                        return Err(Self::Err {
                            kind: WenyanIntErrorKind::InvalidDigit,
                        });
                    }
                }
                None => break,
            }
        }
        result_vec.reverse();
        Ok(WenyanInt {
            data: BigInt::parse_bytes(&result_vec, 10).unwrap() * sign,
        })
    }
}

impl FromPrimitive for WenyanInt {
    fn from_i64(n: i64) -> Option<Self> {
        Some(WenyanInt {
            data: BigInt::from_i64(n).unwrap(),
        })
    }

    fn from_u64(n: u64) -> Option<Self> {
        Some(WenyanInt {
            data: BigInt::from_u64(n).unwrap(),
        })
    }
}
#[test]
fn test_from_str() {
    assert_eq!(
        WenyanInt::from_str("零").unwrap(),
        WenyanInt::from_i32(0).unwrap()
    );
    assert_eq!(
        WenyanInt::from_str("一").unwrap(),
        WenyanInt::from_i32(1).unwrap()
    );
    assert_eq!(
        WenyanInt::from_str("二").unwrap(),
        WenyanInt::from_i32(2).unwrap()
    );
    assert_eq!(
        WenyanInt::from_str("負一").unwrap(),
        WenyanInt::from_i32(-1).unwrap()
    );
}
