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
}

impl ParseWenyanIntError {
    fn __description(&self) -> &str {
        match self.kind {
            WenyanIntErrorKind::Empty => "cannot parse integer from empty string",
            WenyanIntErrorKind::InvalidDigit => "invalid digit found in string",
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
        let mut result = s.to_string();
        for (i, c) in "一二三四五六七八九".chars().enumerate() {
            result = result.replace(c, &(i + 1).to_string());
        }
        Ok(WenyanInt {
            data: BigInt::parse_bytes(result.as_bytes(), 10).unwrap(),
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
        WenyanInt::from_str("一").unwrap(),
        WenyanInt::from_i32(1).unwrap()
    );
    assert_eq!(
        WenyanInt::from_str("二").unwrap(),
        WenyanInt::from_i32(2).unwrap()
    );
}
